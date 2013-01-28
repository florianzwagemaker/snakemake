# -*- coding: utf-8 -*-

import os

from snakemake.workflow import Workflow
from snakemake.exceptions import print_exception
from snakemake.logging import logger, init_logger
from snakemake.persistence import Persistence

__author__ = "Johannes Köster"
__version__ = "2.1.1"


def snakemake(snakefile,
    listrules=False,
    cores=1,
    workdir=None,
    targets=None,
    dryrun=False,
    touch=False,
    forcetargets=False,
    forceall=False,
    forcerules=None,
    prioritytargets=None,
    stats=None,
    printreason=False,
    printshellcmds=False,
    printdag=False,
    nocolor=False,
    quiet=False,
    keepgoing=False,
    cluster=None,
    standalone=False,
    ignore_ambiguity=False,
    snakemakepath=None,
    lock=True,
    cleanup=False):
    """
    Run snakemake on a given snakefile.
    Note: at the moment, this function is not thread-safe!

    Arguments
    snakefile         -- the snakefile.
    list              -- list rules.
    jobs              -- maximum number of parallel jobs (default: 1).
    directory         -- working directory (default: current directory).
    rule              -- execute this rule (default: first rule in snakefile).
    dryrun            -- print the rules that would be executed, but do not execute them.
    forcethis         -- force the selected rule to be executed
    forceall          -- force all rules to be executed
    time_measurements -- measure the running times of all rules
    lock              -- lock the working directory
    """

    init_logger(nocolor=nocolor, stdout=dryrun)

    if not os.path.exists(snakefile):
        logger.error("Error: Snakefile \"{}\" not present.".format(snakefile))
        return False

    if workdir:
        olddir = os.getcwd()
    workflow = Workflow(snakemakepath=snakemakepath)

    if standalone:
        try:
            # set the process group
            os.setpgrp()
        except:
            # ignore: if it does not work we can still work without it
            pass

    success = False
    persistence = Persistence(nolock=not lock or dryrun)
    try:
        workflow.include(snakefile, workdir=workdir, overwrite_first_rule=True)

        if cleanup:
            try:
                persistence.unlock()
            except IOError:
                logger.error("Error: Unlocking the directory {} failed. Maybe "
                "you don't have the permissions?")
                return False
        try:
            persistence.lock()
        except IOError:
            logger.error("Error: Directory cannot be locked. Please make "
                "sure that no other Snakemake process is running on the "
                "following directory:\n{}"
                "If you are sure that no other "
                "instances of snakemake are running on this directory, "
                "the remaining lock was likely caused by a kill signal or "
                "a power loss. It can be removed with "
                "the --cleanup argument.".format(os.getcwd()))
                # TODO provide cleanup
            return False
        workflow.persistence = persistence

        if listrules:
            workflow.list_rules()
            return True

        success = workflow.execute(targets=targets, dryrun=dryrun, touch=touch,
           cores=cores, forcetargets=forcetargets,
           forceall=forceall, forcerules=forcerules,
           prioritytargets=prioritytargets, quiet=quiet, keepgoing=keepgoing,
           printshellcmds=printshellcmds, printreason=printreason,
           printdag=printdag, cluster=cluster,
           ignore_ambiguity=ignore_ambiguity,
           workdir=workdir, stats=stats)

    except (Exception, BaseException) as ex:
        print_exception(ex, workflow.linemaps)
    if workdir:
        os.chdir(olddir)
    if workflow.persistence:
        persistence.unlock()
    return success