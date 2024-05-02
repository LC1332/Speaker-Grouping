import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors
import numpy as np

from AugmentedUnionFind import AugmentedUnionFind


class VideoData:
    def __init__(self, inference_table, folder, previous_tables=[]):

        self.load_inference(inference_table, folder)
        self.load_previous_tables(previous_tables)

        self.M = 5
        self.minimal_self_group_size = 3
        self.name_epsilon = 0.1
        self.stop_threshold = 0.45

    def load_inference(self, inference_table, folder ):

        self.fname_table = inference_table

        # Load the inference table assuming it's already processed and path updated
        self.table = pd.read_parquet(self.fname_table)

        self.folder = folder

        print(f"Inference table loaded from {self.fname_table}")

    def load_previous_tables(self, previous_tables ):
        self.previous_table_fnames = previous_tables
        self.merge_and_clean( previous_tables )

    def merge_and_clean(self, previous_table_fnames):
        # Concatenate all tables if there are previous tables
        if len(previous_table_fnames) == 0:
            self.previous_data = None
            return

        previous_tables = [pd.read_parquet(fname) for fname in previous_table_fnames]

        all_data = pd.concat(previous_tables, ignore_index=True)

        # Clean data: remove rows where '人物' is NA or 'audio_feature' length is 0
        all_data.dropna(subset=['人物'], inplace=True)
        all_data = all_data[all_data['audio_feature'].apply(len) != 0]

        # Assign the cleaned data back to self.table
        self.previous_data = all_data
        print("Data merged and cleaned. Rows with empty '人物' or 'audio_feature' removed.")

    def compute_speaker(self):
        self.build_edge_map()
        self.sort_edges()
        self.group_all()
        self.append_similarity()
        self.compute_knn_result()

    def compute_knn_result(self):
        self.table['knn_speaker'] = "unknown"
        self.table['knn_similarity'] = -1

        if self.previous_data is None:
            return

        for index, edges in self.candidate_edges_on_previous.items():
            if edges:  # Ensure there is at least one edge to process
                top_match_index, top_match_similarity = edges[0]
                speaker_name = self.previous_data.iloc[top_match_index]['人物']
                self.table.at[index, 'knn_speaker'] = speaker_name
                self.table.at[index, 'knn_similarity'] = 1 - top_match_similarity
        print("KNN speakers and similarities computed.")


    def build_edge_map(self):
        # Extract and normalize audio features from self.table
        audio_features_self = np.stack(self.table['audio_feature'])
        norms_self = np.linalg.norm(audio_features_self, axis=1, keepdims=True)
        normalized_audio_features_self = audio_features_self / norms_self

        # Fit and query NearestNeighbors for self.table
        knn_self = NearestNeighbors(n_neighbors=self.M + 1, metric='cosine')
        knn_self.fit(normalized_audio_features_self)
        distances_self, indices_self = knn_self.kneighbors(normalized_audio_features_self)

        # Store the indices and distances for self, ignoring the point itself in the indices
        self.candidate_edges_on_self = {i: list(zip(indices_self[i][1:self.M+1], distances_self[i][1:self.M+1])) for i in range(len(self.table))}

        if self.previous_data is not None:
            # Extract and normalize audio features from self.previous_data
            audio_features_previous = np.stack(self.previous_data['audio_feature'])
            norms_previous = np.linalg.norm(audio_features_previous, axis=1, keepdims=True)
            normalized_audio_features_previous = audio_features_previous / norms_previous

            # Fit and query NearestNeighbors for self.previous_data
            knn_previous = NearestNeighbors(n_neighbors=self.M, metric='cosine')
            knn_previous.fit(normalized_audio_features_previous)
            distances_previous, indices_previous = knn_previous.kneighbors(normalized_audio_features_self)

            # Store the indices and distances for previous data
            self.candidate_edges_on_previous = {i: list(zip(indices_previous[i], distances_previous[i])) for i in range(len(self.table))}
        else:
            self.candidate_edges_on_previous = None

        print("Edge maps built for self and previous data with distances included.")

    def append_similarity(self):
        # Extract the list of unique speakers from previous_data
        if self.previous_data is not None:
            speakers_set = set(self.previous_data['人物'])
        else:
            speakers_set = set()

        # Iterate over each row in self.table to append similarity to the 'estimated_speaker' column
        for idx, row in self.table.iterrows():
            estimated_speaker = row['estimated_speaker']
            if estimated_speaker not in speakers_set:
                # If the estimated speaker is not in the speakers list, continue to next row
                continue

            # Find the first match from self.candidate_edges_on_previous that corresponds to this speaker
            for edge in self.candidate_edges_on_previous.get(idx, []):
                target_index, cosine_distance = edge
                target_speaker = self.previous_data.iloc[target_index]['人物']
                if target_speaker == estimated_speaker:
                    # Calculate the cosine similarity and format it
                    cosine_similarity = 1 - cosine_distance
                    formatted_similarity = "{:.2f}".format(cosine_similarity)
                    self.table.at[idx, 'estimated_speaker'] = f"{estimated_speaker}_{formatted_similarity}"
                    break
            else:
                # If no matching speaker was found, set similarity to 0
                self.table.at[idx, 'estimated_speaker'] = f"{estimated_speaker}_0.00"

        print("Similarity values appended to the estimated speakers.")


    def sort_edges(self):
        # Aggregate and sort edges
        all_edges = []

        # Process edges on self
        for source_index, edges in self.candidate_edges_on_self.items():
            all_edges.extend((source_index, "self", target_index, 1 - dist) for target_index, dist in edges)

        # Process edges on previous if available
        if self.previous_data is not None:
            for source_index, edges in self.candidate_edges_on_previous.items():
                all_edges.extend((source_index, "previous", target_index, 1 - dist) for target_index, dist in edges)

        # Sort edges by similarity (1 - distance) in descending order
        self.sorted_edges = sorted(all_edges, key=lambda x: x[3], reverse=True)
        print("Edges sorted by descending similarity.")

    def group_all(self):
        # Initialize the union-find structure for the size of the table
        uf = AugmentedUnionFind(len(self.table))
        self.table['estimated_speaker'] = None

        # If there are marked '人物' (speaker) values, copy them to 'estimated_speaker'
        if '人物' in self.table.columns:
            self.table['estimated_speaker'] = self.table['人物']

        # Initialize undeal_count and visited list
        undeal_count = len(self.table) - self.table['estimated_speaker'].count()
        visited = [False] * len(self.table)

        count = 0
        count_empty_merge = 0

        # Process each edge in the sorted list
        for source_index, table_type, target_index, similarity in self.sorted_edges:
            if visited[source_index]:
                continue

            if similarity < self.stop_threshold:
                break

            # Check if the node has been dealt with
            root_name = uf.get_root_name(source_index)


            if table_type == "self":
                target_name = uf.get_root_name(target_index)
                if root_name == "default" or target_name == "default" or root_name == target_name:
                    # 这个时候要检查target是不是有root_name
                    uf.union(source_index, target_index, similarity)

                if root_name == "default" and target_name == "default":
                    count_empty_merge += 1

            elif table_type == "previous":
                target_name = self.previous_data.iloc[target_index]['人物']
                last_similarity = uf.get_last_similarity(source_index)

                if similarity >= last_similarity - self.name_epsilon or uf.get_size(source_index) < self.minimal_self_group_size:
                    if root_name == "default":
                        uf.set_root_name(source_index, target_name)

            root_name = uf.get_root_name(source_index)

            if root_name != 'default':
                self.table.at[source_index, 'estimated_speaker'] = root_name

            # continue

            new_size = uf.get_size(source_index)

            if not visited[source_index] and (root_name != "default" or  new_size >= self.minimal_self_group_size):
                visited[source_index] = True
                undeal_count -= 1

            count += 1

            if undeal_count == 0:
                break

        print("无名合并次数", count_empty_merge)
        print("合并次数",count)

        # Final pass to ensure all entries have correct labels
        for i in range(len(self.table)):
            root_name = uf.get_root_name(i)
            if root_name != 'default':
                self.table.at[i, 'estimated_speaker'] = root_name
            else:
                root_id = uf.find(i)
                self.table.at[i, 'estimated_speaker'] = str(root_id)

        print("All groups computed and speakers estimated.")

    # Add this method in the class where you define the rest of your methods.

    def get_current_table(self):
        # Check if 'estimated_speaker' column exists, compute if not
        if 'estimated_speaker' not in self.table.columns:
            self.compute_speaker()

        # Check and select the necessary columns to be returned
        required_columns = ['knn_speaker', 'knn_similarity', 'estimated_speaker', '人物', '人物台词', '开始时间']
        # Ensure that all required columns exist in the DataFrame
        available_columns = [col for col in required_columns if col in self.table.columns]

        # Assemble 'knn_result' from 'knn_speaker' and 'knn_similarity'
        self.table['knn_result'] = self.table['knn_speaker'].astype(str) + "_" + self.table['knn_similarity'].apply(lambda x: f"{x:.2f}")

        # Reset the index to add it as a column in the DataFrame
        result_table = self.table[available_columns + ['knn_result']].reset_index()
        # Rename 'index' column to something more descriptive if desired, e.g., 'Row Index'
        result_table.rename(columns={'index': 'Row Index'}, inplace=True)

        # Reset the index to add it as a column in the DataFrame
        result_table = self.table[['knn_result'] + available_columns].reset_index()
        # Drop 'knn_speaker' and 'knn_similarity' from the result table
        result_table.drop(columns=['knn_speaker', 'knn_similarity'], inplace=True)

        # Rename 'index' column to something more descriptive if desired, e.g., 'Row Index'
        result_table.rename(columns={'index': 'Row Index'}, inplace=True)

        # Move 'Row Index' to be the last column if you want it at the end instead of the beginning
        cols = result_table.columns.tolist()  # Convert columns to list
        # Ensure 'knn_result' is the first column
        cols = [cols[1]] + cols[2:] + [cols[0]]  # Skip 'Row Index' and append it at the end
        result_table = result_table[cols]

        # Return the DataFrame with the modified columns
        return result_table

    def label_row(self, index, speaker, if_return = True):
        # Update the specified row's speaker
        self.table.at[index, '人物'] = speaker

        # Extract the audio feature for the specified index row
        audio_feature_index = np.array(self.table.at[index, 'audio_feature'])

        # Normalize the audio feature vector for cosine similarity calculation
        norm_index = np.linalg.norm(audio_feature_index)
        if norm_index > 0:
            audio_feature_index /= norm_index

        # Iterate over all rows except the index row itself
        for idx, row in self.table.iterrows():
            if idx == index:
                continue

            # Extract and normalize the audio feature of the current row
            audio_feature_current = np.array(row['audio_feature'])
            norm_current = np.linalg.norm(audio_feature_current)
            if norm_current > 0:
                audio_feature_current /= norm_current

            # Calculate cosine similarity
            similarity = np.dot(audio_feature_index, audio_feature_current)

            # Check if this similarity is greater than the existing knn_similarity
            if (similarity > row['knn_similarity'] and self.previous_data is not None) \
                or (similarity > row['knn_similarity'] and similarity > self.stop_threshold) :
                self.table.at[idx, 'knn_speaker'] = speaker
                self.table.at[idx, 'knn_similarity'] = similarity

                # Assemble 'knn_result' from 'knn_speaker' and 'knn_similarity'
                self.table.at[idx, 'estimated_speaker'] = speaker + "_" + f"%.2f" % similarity

        if if_return:
            # Return the updated table
            return self.get_current_table()
        else:
            return None

    def label_rows(self, indexes, speakers ):
        # 这里有点懒了直接批量调用
        for index, speaker in zip(indexes, speakers):
            self.label_row(index, speaker, False)

        return self.get_current_table()
