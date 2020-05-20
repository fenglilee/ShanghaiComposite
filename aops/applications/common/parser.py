#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/24 12:35
# @Author  : szf

"""
Parse csv/txt files uploaded by user.
"""
import csv


class Parser(object):

    def __init__(self, path):
        self.path = path

    def parse(self):
        raise Exception('Please define your parse in children class!!')

    def _to_dict(self, items, header):
        """ return a list that each item is a dict"""
        results = []
        for item in items:
            results.append(dict(zip(header, item)))
        return results


class TextParser(Parser):
    def parse(self):
        results = []
        with open(self.path, 'r') as f:
            data = f.read()
        for line in data.split('\r\n'):
            results.append(line.split())
        return self._to_dict(results[1:], results[0])


class CsvParser(Parser):
    def parse(self, has_annotation=True):
        lines = []
        with open(self.path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
            lines = list(csv_reader)
        if has_annotation:
            cn_keys = lines.pop(0)   # chinese key names
            cn_types = lines.pop(0)    # chinese type explain
        header = lines[0]              # english key names
        content = lines[1:]

        return self._to_dict(content, header)


if __name__ == '__main__':
    import os
    csv_path = os.path.join(os.getenv('DEPLOY_ROOT_DIR'), 'aops', 'upload_files', 'host', 'inst_vm_public_cloud.CSV')
    # print CsvParser(csv_path).parse()

    text_path = os.path.join(os.getenv('DEPLOY_ROOT_DIR'), 'aops', 'upload_files', 'host', 'accounts.txt')
    print TextParser(text_path).parse()


