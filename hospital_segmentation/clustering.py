# -*- coding: utf-8 -*-

import itertools
import logging
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

class HospitalClustering:

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def run(self, feat_df):
        self._logger.debug("begin clustering")

        # category2: notice_no=2x
        df_categ2 = pd.DataFrame(feat_df[feat_df.notice_no.str.startswith('2')])
        qty = int(len(df_categ2)/8)
        model = KMeans(n_clusters=qty, random_state=10)
        clusters = model.fit(df_categ2.iloc[:, 4:])
        df_categ2['cluster'] = clusters.labels_
        self._to_csv(df_categ2, 'categ2_df.csv')
        # self._logger.debug(df_categ2)

        # category3: notice_no=3x,9x,0x
        df_categ3 = pd.DataFrame(feat_df[feat_df.notice_no.str.match(r'^[^12]{1}\d+$')])
        qty = int(len(df_categ3)/8)
        model = KMeans(n_clusters=qty, random_state=10)
        clusters = model.fit(df_categ3.iloc[:, 4:])
        df_categ3['cluster'] = clusters.labels_
        self._to_csv(df_categ3, 'categ3_df.csv')
        # self._logger.debug(df_categ3)

    def run_each_position(self, feat_df):
        self._logger.debug("begin clustering w/ position_kbn")

        # category2: notice_no=2x
        df_categ2 = pd.DataFrame(feat_df[feat_df.notice_no.str.startswith('2')])
        df_categ2 = df_categ2.groupby('posit_kbn').apply(self._clustering_wt_posit)

        # self._to_csv(df_categ2, 'wt_posit_categ2_df.csv')
        self._test_show_plot(df_categ2)

    def _clustering_wt_posit(self, grouped_df):

        self._logger.debug(f"groupby={grouped_df.name}: {len(grouped_df)}")
        qty = int(len(grouped_df)/5)
        model = KMeans(n_clusters=qty, random_state=10)
        clusters = model.fit(grouped_df.iloc[:, 4:-1])
        grouped_df['cluster'] = clusters.labels_

        return grouped_df

    def _test_show_plot(self, df_categ: pd.DataFrame):

        df = df_categ[df_categ['posit_kbn'] == '211']
        clusters = df['cluster'].unique()
        fig, axes = plt.subplots(nrows=len(clusters), ncols=10, sharey=True)
        for r_now, cluster_v in enumerate(clusters):
            clust_df = df[df['cluster'] == cluster_v]
            clust_df['mdc01_wo_ope'].plot(ax=axes[r_now, 0], legend=False, kind='bar')
            clust_df['mdc02_wo_ope'].plot(ax=axes[r_now, 1], legend=False, kind='bar')
            clust_df['mdc03_wo_ope'].plot(ax=axes[r_now, 2], legend=False, kind='bar')
            clust_df['mdc04_wo_ope'].plot(ax=axes[r_now, 3], legend=False, kind='bar')
            clust_df['mdc05_wo_ope'].plot(ax=axes[r_now, 4], legend=False, kind='bar')
            clust_df['mdc06_wo_ope'].plot(ax=axes[r_now, 5], legend=False, kind='bar')
            clust_df['mdc07_wo_ope'].plot(ax=axes[r_now, 6], legend=False, kind='bar')
            clust_df['mdc08_wo_ope'].plot(ax=axes[r_now, 7], legend=False, kind='bar')
            clust_df['mdc09_wo_ope'].plot(ax=axes[r_now, 8], legend=False, kind='bar')
            clust_df['mdc10_wo_ope'].plot(ax=axes[r_now, 9], legend=False, kind='bar')

        plt.show()

    def _to_csv(self, df: pd.DataFrame, filename: str):
        if len(df) == 0:
            return

        file_path = f"tmp/{filename}"
        if os.path.exists(file_path):
            os.remove(file_path)

        df.to_csv(file_path)
        self._logger.debug(f"output {file_path}")
