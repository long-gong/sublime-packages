# ST2/ST3 compat
import sublime
if sublime.version() < '3000':
    # we are on ST2 and Python 2.X
    _ST3 = False
    strbase = basestring

    # reraise implementation from 6
    exec("""def reraise(tp, value, tb=None):
    raise tp, value, tb
""")
else:
    _ST3 = True
    strbase = str

    # reraise implementation from 6
    def reraise(tp, value, tb=None):
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

import os
import re
import subprocess
import sys
# This will work because makePDF.py puts the appropriate
# builders directory in sys.path
from pdfBuilder import PdfBuilder

from latextools_utils.external_command import external_command, get_texpath


# Standard LaTeX warning
CITATIONS_REGEX = re.compile(
    r"Warning: Citation [`|'].+' (?:on page \d+ )?undefined")
# Capture which program to run for BibLaTeX
BIBLATEX_REGEX = re.compile(
    r"Package biblatex Warning: Please \(re\)run (\S*)")
# Used to indicate a subdirectory that needs to be made for a file input using
# \include
FILE_WRITE_ERROR_REGEX = re.compile(
    r"! I can't write on file `(.*)/([^/']*)'")


# ----------------------------------------------------------------
# EdasBuilder class
#
# This is a more fully functional verion of the Simple Builder
# concept. It implements the same building features as the
# Traditional builder.
#
class EdasBuilder(PdfBuilder):

    def __init__(self, *args):
        super(EdasBuilder, self).__init__(*args)
        self.name = "Edas Builder (dvi->ps->pdf)"
        self.bibtex = self.builder_settings.get('bibtex', 'bibtex')
        self.ps2pdf = self.builder_settings.get('ps2pdf', None)
        self.display_log = self.builder_settings.get("display_log", False)
        self.plat = sublime.platform()

    def commands(self):
        # Print greeting
        self.display("\n\nEdas Builder (dvi->ps->pdf): ")

        engine = u'latex'
        latex = [engine, u"-interaction=nonstopmode", u"-synctex=1"]
        # texliveonfly = [TEXLIVEONFLY, u"-interaction=nonstopmode", u"-synctex=1"]
        biber = [u"biber"]
        ps2pdf = [self.ps2pdf if self.ps2pdf else
                  (u'gs' if self.plat != 'windows' else u'gswin64c'),
                  u'-dNOPAUSE', u'-dBATCH', u'-dPDFSETTINGS=/prepress', u'-dCompatibilityLevel=1.4',
                  u'-dSubsetFonts=true', u'-dEmbedAllFonts=true', u'-sDEVICE=pdfwrite',
                  u'-sOutputFile=\"{tex_name}.pdf\"'.format(tex_name=self.job_name), u'-c', u'save pop', u'-f',
                  u'\"{tex_name}.ps\"'.format(tex_name=self.job_name)]
        dvips = [u'dvips', u'{tex_name}.dvi'.format(tex_name=self.job_name)]

        if self.aux_directory is not None:
            biber.append(u'--output-directory=' + self.aux_directory)
            if self.aux_directory == self.output_directory:
                latex.append(u'--output-directory=' + self.aux_directory)
            else:
                latex.append(u'--aux-directory=' + self.aux_directory)
        elif self.output_directory is not None:
            biber.append(u'--output-directory=' + self.output_directory)

        if (
            self.output_directory is not None and
            self.output_directory != self.aux_directory
        ):
            latex.append(u'--output-directory=' + self.output_directory)

        if self.job_name != self.base_name:
            latex.append(u'--jobname=' + self.job_name)

        for option in self.options:
            latex.append(option)

        latex.append(self.tex_name)

        # Check if any subfolders need to be created
        # this adds a number of potential runs as LaTeX treats being unable
        # to open output files as fatal errors
        output_directory = (
            self.aux_directory_full or self.output_directory_full
        )

        if (
            output_directory is not None and
            not os.path.exists(output_directory)
        ):
            self.make_directory(output_directory)

        yield (latex, "running {0}...".format(engine))
        self.display("done.\n")
        self.log_output()

        if output_directory is not None:
            while True:
                start = 0
                added_directory = False
                while True:
                    match = FILE_WRITE_ERROR_REGEX.search(self.out, start)
                    if match:
                        self.make_directory(
                            os.path.normpath(
                                os.path.join(
                                    output_directory,
                                    match.group(1)
                                )
                            )
                        )
                        start = match.end(1)
                        added_directory = True
                    else:
                        break
                if added_directory:
                    yield (latex, "running {0}...".format(engine))
                    self.display("done.\n")
                    self.log_output()
                else:
                    break

        # if get_platform() != u'windows' and FILE_NOT_FOUND_ERROR_REGEX.search(self.out):
        #     texliveonfly.append(u'--jobname=' + self.job_name)
        #     texliveonfly.append(self.tex_name)
        #     yield(texliveonfly, 'running {0}'.format(u'texliveonfly'))
        # else:
        #     windows_cmd = DEFAULT_COMMAND_WINDOWS_MIKTEX
        #     for i, c in enumerate(windows_cmd):
        #         windows_cmd[i] = c.replace(
        #             "-%E", "-" + engine if engine != 'pdflatex' else '-pdf'
        #         ).replace("%E", engine)
        #     yield (windows_cmd + [self.tex_name], "Invoking " + windows_cmd[0] + "... ")
            
        # Check for citations
        # We need to run pdflatex twice after bibtex
        run_bibtex = False
        use_bibtex = True
        bibtex = None
        if CITATIONS_REGEX.search(self.out):
            run_bibtex = True
            # are we using biblatex?
            m = BIBLATEX_REGEX.search(self.out)
            if m:
                bibtex = m.group(1).lower()
                if bibtex == 'biber':
                    use_bibtex = False
        # check for natbib as well
        elif (
            'Package natbib Warning: There were undefined citations'
                in self.out):
            run_bibtex = True

        if run_bibtex:
            if use_bibtex:
                yield (
                    self.run_bibtex(bibtex),
                    "running {0}...".format(bibtex or 'bibtex')
                )
            else:
                yield (biber + [self.job_name], 'running biber...')

            self.display('done.\n')
            self.log_output()

            for i in range(2):
                yield (latex, "running {0}...".format(engine))
                self.display("done.\n")
                self.log_output()

        # Check for changed labels
        # Do this at the end, so if there are also citations to resolve,
        # we may save one pdflatex run
        if "Rerun to get cross-references right." in self.out:
            yield (latex, "running {0}...".format(engine))
            self.display("done.\n")
            self.log_output()

        # Run dvips
        yield(dvips, "running dvips ...")

        # Run gs
        yield(ps2pdf, "running ps2pdf ...")

    def log_output(self):
        if self.display_log:
            self.display("\nCommand results:\n")
            self.display(self.out)
            self.display("\n\n")

    def make_directory(self, directory):
        if not os.path.exists(directory):
            try:
                print('making directory ' + directory)
                os.makedirs(directory)
            except OSError:
                if not os.path.exists(directory):
                    reraise(*sys.exc_info())

    def run_bibtex(self, command=None):
        if command is None:
            command = [self.bibtex]
        elif isinstance(command, strbase):
            command = [command]

        # to get bibtex to work with the output directory, we change the
        # cwd to the output directory and add the main directory to
        # BIBINPUTS and BSTINPUTS
        env = dict(os.environ)
        cwd = self.tex_dir

        output_directory = (
            self.aux_directory_full or self.output_directory_full
        )
        if output_directory is not None:
            # cwd is, at the point, the path to the main tex file
            if _ST3:
                env['BIBINPUTS'] = cwd + os.pathsep + env.get('BIBINPUTS', '')
                env['BSTINPUTS'] = cwd + os.pathsep + env.get('BSTINPUTS', '')
            else:
                env['BIBINPUTS'] = \
                    (cwd + os.pathsep + env.get('BIBINPUTS', '')).encode(
                        sys.getfilesystemencoding())
                env['BSTINPUTS'] = \
                    (cwd + os.pathsep + env.get('BSTINPUTS', '')).encode(
                        sys.getfilesystemencoding())
            # now we modify cwd to be the output directory
            # NOTE this cwd is not reused by any of the other command
            cwd = output_directory
        env['PATH'] = get_texpath()

        command.append(self.job_name)
        return external_command(
            command,
            env=env,
            cwd=cwd,
            preexec_fn=os.setsid if self.plat != 'windows' else None,
            use_texpath=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )