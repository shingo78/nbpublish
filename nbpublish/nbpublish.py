#!/usr/bin/env python

import io
import os
import os.path
import sys
import tempfile
import shutil

import nbformat

from traitlets.config.application import catch_config_error
from traitlets.config.application import Application

from traitlets import Int, Bool, Unicode, Dict, default


class NotebookPublishCleaner(Application):
    '''Notebook cleaner to publish'''
    name = 'notebook publish cleaner'
    description = (
        'Utility for cleaning up outputs and metadata'
        'in the notebook')
    examples = ""

    trim_history = Int(
        None, min=0, allow_none=True,
        help=(
            'Max size of cell meme history for trimming, '
            'by default do nothing')
    ).tag(config=True)

    trim_server_signature = Int(
        None, min=0, allow_none=True,
        help=(
            'Max size of server signature history for trimming, '
            '0 means delete completely, by default do nothing')
    ).tag(config=True)

    output_dir = Unicode(help='Output directory.').tag(config=True)

    clear_output = Bool(False,
                        help='Clear cell outputs.').tag(config=True)
    tree = Bool(False,
                help='Keep tree layout of source files.').tag(config=True)

    aliases = Dict({
        'trim-history': 'NotebookPublishCleaner.trim_history',
        'trim-server-signature': 'NotebookPublishCleaner.trim_server_signature',
        'output-dir': 'NotebookPublishCleaner.output_dir'
    })

    flags = Dict({
        'clear-output': ({
                'NotebookPublishCleaner': {'clear_output': True}
        }, 'Clear cell outputs'),
        'tree': ({
                'NotebookPublishCleaner': {'tree': True}
        }, 'Keep tree layout of source files.')
    })

    @default('output_dir')
    def _default_output_dir(self):
        return os.getcwd()

    @catch_config_error
    def initialize(self, argv=None):
        super(NotebookPublishCleaner, self).initialize(argv)

    def start(self):
        if len(self.extra_args) == 0:
            self.print_help()
            sys.exit(-1)

        results = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for src in self.extra_args:
                src_dir, fname = os.path.split(src)
                temp_dest = tempfile.NamedTemporaryFile(
                    dir=temp_dir,
                    delete=False)
                self.log.debug('cleaning %s -> %s', src, temp_dest.name)
                results.append(
                    self._clean(src, temp_dest.name)
                )

            for src, temp_file in results:
                src_dir, fname = os.path.split(src)
                shutil.copymode(src, temp_file)
                if self.tree:
                    src_common_path = os.path.commonpath(self.extra_args)
                    src_relpath = os.path.relpath(src, start=src_common_path)
                    output_file = os.path.join(self.output_dir, src_relpath)
                    self.log.debug('copy %s -> %s', temp_file, output_file)
                    output_file_parent_dir, _ = os.path.split(output_file)
                    os.makedirs(output_file_parent_dir, exist_ok=True)
                    shutil.copy(temp_file, output_file)
                else:
                    output_file = os.path.join(self.output_dir, fname)
                    self.log.debug('copy %s -> %s', temp_file, output_file)
                    shutil.copy(temp_file, output_file)

    def _clean(self, src, dest):

        src = os.path.normcase(os.path.normpath(src))
        dest = os.path.normcase(os.path.normpath(dest))

        with io.open(src, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        for cell in nb.cells:
            self._clear_lc_wrapper(nb, cell)
            self._clear_fronzon_cell(nb, cell)
            self._trim_meme_history(nb, cell)
            self._clear_outputs(nb, cell)

        self._clear_server_signature(nb)

        with io.open(dest, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)

        return (src, dest)

    def _clear_fronzon_cell(self, nb, cell):
        if 'run_through_control' in cell.metadata:
            run_through_control = cell.metadata['run_through_control']
            run_through_control['frozen'] = False

    def _trim_meme_history(self, nb, cell):
        if self.trim_history is None:
            return
        if 'lc_cell_meme' in cell.metadata:
            cell_meme = cell.metadata['lc_cell_meme']
            if 'history' in cell_meme:
                history = cell_meme['history']
                cell_meme['history'] = history[-self.trim_history:]

    def _clear_lc_wrapper(self, nb, cell):
        if 'lc_wrapper' in cell.metadata:
            del cell.metadata['lc_wrapper']

    def _clear_outputs(self, nb, cell):
        if not self.clear_output:
            return
        if cell['cell_type'] == 'code':
            cell['execution_count'] = None
            cell['outputs'] = []

            if 'pinned_outputs' in cell.metadata:
                del cell.metadata['pinned_outputs']

    def _clear_server_signature(self, nb):
        if self.trim_server_signature is None:
            return

        if 'lc_notebook_meme' in nb.metadata:
            nb_meme = nb.metadata['lc_notebook_meme']

            if self.trim_server_signature == 0:
                if 'lc_server_signature' in nb_meme:
                    del nb_meme['lc_server_signature']
            else:
                self._trim_server_signature_history(nb_meme)

    def _trim_server_signature_history(self, nb_meme):
        if 'lc_server_signature' not in nb_meme:
            return

        server_signature = nb_meme['lc_server_signature']
        if 'history' not in server_signature:
            return

        history = server_signature['history']
        server_signature['history'] = history[-self.trim_server_signature]


def main():
    NotebookPublishCleaner.launch_instance()
