# -*- coding: utf-8 -*-

import itertools
import logging
import os
import pandas as pd
import numpy as np
import openpyxl as xl

class FeatureGenerator:

    def __init__(self):
        self._logger = logging.getLogger(__name__)

        self.filepath_overview_excel = ""
        self.filepath_mdc_rate_excel = ""
        self.filepath_med_area2 = ""

    def run(self, vervbose: bool = False) -> pd.DataFrame:
        """
        Generate features
        """

        # features: MDC rate
        f_list = self._parse_mdc_rate_file(self.filepath_mdc_rate_excel, vervbose)
        colnames = ["notice_no"] + \
            [f"mdc{i:0>2}_wo_ope" for i in range(1, 19)] + [f"mdc{i:0>2}_w_ope" for i in range(1, 19)]
        df = pd.DataFrame(f_list, columns=colnames)
        # remove if all mdc rate are 0
        df = df.loc[(df.iloc[:, 1:] != 0).any(axis=1)]
        # self._logger.debug(df)

        # features: overview(dpc bed qty)
        overview_df = self._parse_overview_file(self.filepath_overview_excel, vervbose)
        # remove columns if not used
        overview_df.drop(columns="bed_qty", inplace=True)

        # merge
        feat_df = pd.merge(overview_df, df, on="notice_no")

        med_area2_df = self._load_medical_area2(self.filepath_med_area2, vervbose)
        # merge
        feat_df = pd.merge(feat_df, med_area2_df, on="town_no")

        #
        feat_df['catg_kbn'] = feat_df.groupby('med_area2_no').apply(self._get_posit_within_area2)['catg_kbn']
        self._logger.debug(feat_df)

        if vervbose:
            self._logger.debug(feat_df)

        return feat_df

    def _get_posit_within_area2(self, grouped_df):
        # self._logger.debug(grouped_df)
        grouped_df['catg_kbn'] = '0'

        # category1: notice_no=1x
        df_catg1 = grouped_df[grouped_df.notice_no.str.startswith('1')]
        catg1_exists = len(df_catg1) >= 1
        if len(df_catg1) == 1:
            grouped_df.loc[grouped_df.index.isin(df_catg1.index), 'catg_kbn'] = '10'
        elif catg1_exists:
            grouped_df.loc[grouped_df.index.isin(df_catg1.index), 'catg_kbn'] = '11'

        # category2: notice_no=2x
        df_catg2 = grouped_df[grouped_df.notice_no.str.startswith('2')].sort_values(by='dpc_bed_qty', ascending=False)
        catg2_exists = len(df_catg2) >= 1
        if catg2_exists:
            if len(df_catg2) >= 2:
                grouped_df.loc[grouped_df.index.isin(df_catg2.index), 'catg_kbn'] = '212' if catg1_exists else '202'
            # top1
            grouped_df.loc[grouped_df.index.isin(df_catg2.head(1).index), 'catg_kbn'] = '211' if catg1_exists else '201'

        # category3: notice_no=3x,9x,0x
        df_catg3 = grouped_df[grouped_df.notice_no.str.match(
            r'^[^12]{1}\d+$')].sort_values(by='dpc_bed_qty', ascending=False)
        if len(df_catg3) >= 2:
            grouped_df.loc[grouped_df.index.isin(df_catg3.index),
                           'catg_kbn'] = '312' if catg1_exists or catg2_exists else '302'
            if len(df_catg3) >= 5:
                # percentile
                df_catg3_pct = df_catg3.rank(pct=True, method='min', ascending=False)
                grouped_df.loc[grouped_df.index.isin(df_catg3_pct[df_catg3_pct['dpc_bed_qty'] > 0.6].index),
                               'catg_kbn'] = '313' if catg1_exists or catg2_exists else '303'
        if len(df_catg3) >= 1:
            # top1
            grouped_df.loc[grouped_df.index.isin(df_catg3.head(1).index),
                           'catg_kbn'] = '311' if catg1_exists or catg2_exists else '301'

        return grouped_df

    def _parse_overview_file(self, excel_file_path: str, vervbose: bool = False) -> pd.DataFrame:
        """
        Create pandas.Dataframe from the overview excel file.
        Removed if dpc bed qty is zero.
        """

        if not excel_file_path:
            raise Exception(f"filepath of overview is not set.")

        if not os.path.exists(excel_file_path):
            raise Exception(f"file not found :{excel_file_path}")

        df = pd.read_excel(excel_file_path, sheet_name="施設概要表", header=None,
                           usecols=[0, 1, 2, 4, 6, 14], skiprows=1,
                           names=["notice_no", "prev_notice_no", "town_no", "hosp_name", "dpc_bed_qty", "bed_qty"],
                           dtype={"notice_no": str, "prev_notice_no": str, "town_no": str}, na_filter=False)

        # replace '-' with null
        # df["prev_notice_no"].replace('-', np.nan, inplace=True)
        # remove foot-note
        df = df[df.notice_no.str.isdigit()]

        # remove if dpc_bed are zero
        df = df[df.dpc_bed_qty != 0]

        if vervbose:
            self._logger.debug(df)

        self._logger.debug("fin. parse the overview excel")
        return df

    def _parse_mdc_rate_file(self, excel_file_path: str, vervbose: bool = False) -> list:

        if not excel_file_path:
            raise Exception(f"filepath of MDC rate is not set.")

        if not os.path.exists(excel_file_path):
            raise Exception(f"file not found :{excel_file_path}")

        # https://openpyxl.readthedocs.io/en/stable/index.html
        wb = xl.load_workbook(excel_file_path, read_only=True)

        for try_sheetname in ("割合", "割合 ", " 割合", " 割合 "):
            if try_sheetname in wb.sheetnames:
                ws = wb[try_sheetname]
                break

        if not ws:
            raise Exception(f"this excel file does not contains 割合 worksheet. :{excel_file_path}")

        rows_list = []
        r_l = []
        for r_i, row in enumerate(ws.rows):
            if r_i >= 3:
                # row is tuple of cells
                if row[0].value:
                    # row-header(notice_no,prev_notice_no,hosp_name) and mdc rate w/o ope
                    # r_l = [row[0].value, row[1].value, row[2].value] + \
                    r_l = [row[0].value] + \
                        [row[i].value if row[i].value != '-' else 0 for i in range(4, 22)]
                else:
                    # mdc rate w/ ope
                    r_l += [row[i].value if row[i].value != '-' else 0 for i in range(4, 22)]
                    rows_list.append(r_l)

        if vervbose:
            self._logger.debug(rows_list)
            # self._logger.debug(rows_list[-3:])

        self._logger.debug("fin. load MDC rate excel file.")
        return rows_list

    def _load_medical_area2(self, csv_file_path: str, vervbose: bool = False) -> pd.DataFrame:

        if not csv_file_path:
            raise Exception(f"filepath of medical area2 is not set.")

        if not os.path.exists(csv_file_path):
            raise Exception(f"file not found :{csv_file_path}")

        df = pd.read_csv(csv_file_path, header=None, usecols=[0, 2],
                         names=['town_no', 'med_area2_no'], dtype=str, na_filter=False)

        if vervbose:
            self._logger.debug(df)

        self._logger.debug("fin. load medical area2 csv.")
        return df
