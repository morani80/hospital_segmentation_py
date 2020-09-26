# -*- coding: utf-8 -*-

import unittest
import logging
from hospital_segmentation.feature_generator import FeatureGenerator

class TestFeatureGenerator(unittest.TestCase):

    def test_parse_overview_file(self):
        gener = FeatureGenerator()
        gener._parse_overview_file(r".\in_data\2018(H30)_0_施設概要表.xlsx", vervbose=True)

    def test_parse_mdc_rate_file(self):
        gener = FeatureGenerator()
        gener._parse_mdc_rate_file(r".\in_data\2018(H30_)2-2_MDC別医療機関別件数割合.xlsx", vervbose=True)

    def test_load_medical_area2(self):
        gener = FeatureGenerator()
        gener._load_medical_area2(r".\in_data\med_area2_2017.csv", vervbose=True)

    def setUp(self):

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)  # change the level
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        self._logger.addHandler(handler)
