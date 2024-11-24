#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   get_headers.py
@Time    :   2024/11/24 17:41:03
@Author  :   Ferret@NJTech 
@Version :   1.0
@Contact :   Ferret@NJTech
@License :   (C)Copyright 2024, Ferret@NJTech
@Desc    :   补充描述 
'''

from datetime import datetime
import os
import logging
import subprocess
import pathlib
import shutil
import re

START = datetime.now()
thisScript = pathlib.Path(__file__)
logLevel = logging.INFO
logFile = thisScript.with_suffix('.log')
root = thisScript.parent

# fmt:off
# Basic logging configuration
logging.basicConfig(
    level=logLevel,
    format='%(message)s' if logLevel == logging.INFO else '%(asctime)s %(filename)s(%(lineno)04d) [%(levelname)-8s]: %(message)s',
    handlers=[logging.FileHandler(logFile, mode='w', encoding='utf-8'), logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S'
)
# fmt:on

logger = logging.getLogger(__name__)


def getAllClasses(header_file):
    # 从文件中读取所有类名，作为头文件的文件名
    content = header_file.open(encoding='utf-8').read()
    # 匹配类定义, 两种情形，派生类和非派生类
    patt = re.compile(r'\nclass\s+([a-zA-Z0-9_]+)\s*:?')
    classes = patt.findall(content)
    return classes


def copy_lib(base_dir: pathlib.Path, lib_dump_dir: pathlib.Path):
    lib_dir = base_dir.joinpath('build/lib')
    lib_dump_dir = lib_dump_dir.joinpath('lib')
    lib_dump_dir.mkdir(parents=True, exist_ok=True)
    for lib in lib_dir.rglob('lib*.a'):
        copyto = lib_dump_dir / lib.name
        shutil.copy(lib, copyto)


def copy_doc(base_dir: pathlib.Path, doc_dump_dir: pathlib.Path):
    doc_dir = base_dir.joinpath('build/doc')
    doc_dump_dir = doc_dump_dir.joinpath('doc')
    doc_dump_dir.mkdir(parents=True, exist_ok=True)
    for doc in doc_dir.rglob('*.qch'):
        copyto = doc_dump_dir / doc.name
        shutil.copy(doc, copyto)


def read_old_include(old_include_dir: pathlib.Path):
    lines = []
    for p in old_include_dir.glob('QSint*'):
        if p.is_file():
            with p.open('r', encoding='utf-8') as f:
                lines.extend(f.readlines())

    lines = [line.split('../src/')[-1].strip()[:-1] for line in lines]
    return lines


def main():

    header_dir = root / 'src'
    dump_dir = root / 'qsint'
    if dump_dir.exists():
        shutil.rmtree(dump_dir)
    header_dump_dir = dump_dir / 'include'

    # 从原项目的include中读取3个QSint开头的头文件
    # 列出所有需要生成包含的头文件
    need_headers = read_old_include(root / 'include')
    # logger.info(f'需要的头文件：{need_headers}')

    group = ''
    for header in header_dir.rglob('*.h'):
        # 将所有头文件copy至分组中(所在的目录名为分组)
        new_group = header.parent.name
        if group != new_group:
            group = new_group
            logger.info(
                f'\n-------------------------------------  分组: {group} --------------------------------------'
            )
        sub_dir = header_dump_dir.joinpath(group)
        sub_dir.mkdir(parents=True, exist_ok=True)
        copyto = sub_dir / header.name
        shutil.copy(header, copyto)

        if f'{group}/{header.name}' in need_headers:
            # 生成qsint头文件, 以类为名, 不带.h (类似Qt)
            qsint_classes = getAllClasses(header)
            if qsint_classes:
                # logger.info(f' -> {header.name:20s} 中包含的类：{qsint_classes}')
                # 找到与文件名相同的类，并生成头文件
                same_name_class = [c for c in qsint_classes if c.upper() == header.name[:-2].upper()]
                if same_name_class:
                    logger.info(
                        f' -> 头文件 {same_name_class[0]:20s} 来自 {header.name:22s} (包含的类：{qsint_classes})'
                    )
                    raw_name = sub_dir.joinpath(same_name_class[0])
                    with raw_name.open('w', encoding='utf-8') as f:
                        f.write(f'#include "./{copyto.relative_to(sub_dir).as_posix()}"')
                else:
                    logger.fatal(f' -> {header.name:20s} 未找到与头文件同名的类(包含的类：{qsint_classes})')

    copy_lib(root, dump_dir)
    copy_doc(root, dump_dir)
    logger.info(f'---------------------------------------  end --------------------------------------------')
    shutil.copy(logFile, dump_dir / 'description.txt')


if __name__ == '__main__':
    # fmt: off
    logger.info('脚本 %s 开始运行, 时间：%s ' %(thisScript.name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    main()
    logger.info('脚本 %s 运行完成, 时间：%s ' %(thisScript.name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    # fmt: on
