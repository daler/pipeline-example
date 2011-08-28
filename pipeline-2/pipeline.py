#!/usr/bin/python

from ruffus import *
import yaml

import tasks

module_name = 'pipeline'

# ruffus pipeline skeleton with logging, modified from
# http://www.ruffus.org.uk/examples/code_template/code_template.html
if __name__ == '__main__':
    from ruffus.proxy_logger import *

    def get_options():
        from argparse import ArgumentParser
        import StringIO

        parser = ArgumentParser(usage="\n\n    %(prog)s [arguments]")
        parser.add_argument("-v", "--verbose", dest="verbose",
                          action="count", default=0,
                          help="Print more verbose messages for each "
                               "additional verbose level.")
        parser.add_argument("-L", "--log_file", dest="log_file",
                          metavar="FILE",
                          type=str,
                          help="Name and path of log file")
        parser.add_argument("-t", "--target_tasks", dest="target_tasks",
                            action="append",
                            default=list(),
                            metavar="JOBNAME",
                            type=str,
                            help="Target task(s) of pipeline.")
        parser.add_argument("-j", "--jobs", dest="jobs",
                            default=6,
                            metavar="N",
                            type=int,
                            help="Allow N jobs (commands) to run "
                                 "simultaneously.")
        parser.add_argument("-n", "--just_print", dest="just_print",
                            action="store_true", default=False,
                            help="Don't actually run any commands; just print "
                                 "the pipeline.")
        parser.add_argument("--flowchart", dest="flowchart",
                            metavar="FILE",
                            type=str,
                            help="Don't actually run any commands; just print "
                                 "the pipeline as a flowchart.")
        parser.add_argument("--key_legend_in_graph",
                            dest="key_legend_in_graph",
                            action="store_true",
                            default=False,
                            help="Print out legend and key for dependency "
                                 "graph.")
        parser.add_argument("--forced_tasks", dest="forced_tasks",
                            action="append",
                            default=list(),
                            metavar="JOBNAME",
                            type=str,
                            help="Pipeline task(s) which will be included "
                                 "even if they are up to date.")
        parser.add_argument('--config',
                            help='Meta YAML config')

        # get help string
        f = StringIO.StringIO()
        parser.print_help(f)
        helpstr = f.getvalue()
        options = parser.parse_args()

        mandatory_options = ['config']

        def check_mandatory_options(options, mandatory_options, helpstr):
            """
            Check if specified mandatory options have been defined
            """
            missing_options = []
            for o in mandatory_options:
                if not getattr(options, o):
                    missing_options.append("--" + o)

            if not len(missing_options):
                return

            raise Exception("Missing mandatory parameter%s: %s.\n\n%s\n\n" %
                            ("s" if len(missing_options) > 1 else "",
                             ", ".join(missing_options),
                             helpstr))
        check_mandatory_options(options, mandatory_options, helpstr)
        return options

    def make_logger(options):
        import logging
        import logging.handlers

        MESSAGE = 15
        logging.addLevelName(MESSAGE, "MESSAGE")

        def setup_std_logging(logger, log_file, verbose):
            """
            set up logging using programme options
            """
            class debug_filter(logging.Filter):
                """
                Ignore INFO messages
                """
                def filter(self, record):
                    return logging.INFO != record.levelno

            class NullHandler(logging.Handler):
                """
                for when there is no logging
                """
                def emit(self, record):
                    pass

            # We are interested in all messages
            logger.setLevel(logging.DEBUG)
            has_handler = False

            # log to file if that is specified
            if log_file:
                handler = logging.FileHandler(log_file, delay=False)
                handler.setFormatter(
                    logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)6s - %(message)s"))
                handler.setLevel(MESSAGE)
                logger.addHandler(handler)
                has_handler = True

            # log to stderr if verbose
            if verbose:
                stderrhandler = logging.StreamHandler(sys.stderr)
                stderrhandler.setFormatter(
                        logging.Formatter("    %(message)s")
                        )
                stderrhandler.setLevel(logging.DEBUG)
                if log_file:
                    stderrhandler.addFilter(debug_filter())
                logger.addHandler(stderrhandler)
                has_handler = True

            # no logging
            if not has_handler:
                logger.addHandler(NullHandler())

        # set up log
        logger = logging.getLogger(module_name)
        setup_std_logging(logger, options.log_file, options.verbose)

        # Allow logging across Ruffus pipeline
        def get_logger(logger_name, args):
            return logger

        (logger_proxy,
         logging_mutex) = make_shared_logger_and_proxy(get_logger,
                                                       module_name,
                                                       {})

        return logger_proxy, logging_mutex

    options = get_options()
    logger_proxy, logging_mutex = make_logger(options)

def report(result):
    result.report(logger_proxy, logging_mutex)

config = yaml.load(open(options.config).read())

# begin the pipeline

@files(list(tasks.fastq_to_other_files(config, extension='.clipped')))
def clip(infile, outfile):
    result = tasks.clip(infile, outfile, config)

@transform(clip, suffix('.clipped'), '.clipped.bowtie.sam')
def map(infile, outfile):
    result = tasks.bowtie(infile, outfile, config)
    report(result)

@transform(map, suffix('.bowtie.sam'), '.bowtie.sam.count')
def count(infile, outfile):
    result = tasks.count(infile, outfile, config)
    report(result)

if __name__ == '__main__':

    if options.just_print:
        pipeline_printout(sys.stdout,
                          options.target_tasks,
                          options.forced_tasks,
                          verbose=options.verbose)

    elif options.flowchart:
        pipeline_printout_graph(open(options.flowchart, "w"),
                                os.path.splitext(options.flowchart)[1][1:],
                                options.target_tasks,
                                options.forced_tasks,
                                no_key_legend=not options.key_legend_in_graph)
    else:
        pipeline_run(options.target_tasks,
                     options.forced_tasks,
                     multiprocess=options.jobs,
                     logger=stderr_logger,
                     verbose=options.verbose)

