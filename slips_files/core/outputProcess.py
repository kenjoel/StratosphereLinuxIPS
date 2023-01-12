# Stratosphere Linux IPS. A machine-learning Intrusion Detection System
# Copyright (C) 2021 Sebastian Garcia

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# Contact: eldraco@gmail.com, sebastian.garcia@agents.fel.cvut.cz, stratosphere@aic.fel.cvut.cz
from slips_files.core.database.database import __database__
from slips_files.common.slips_utils import utils
import multiprocessing
import sys
import io
from pathlib import Path
from datetime import datetime
import os
import traceback

# Output Process
class OutputProcess(multiprocessing.Process):
    """
    A class to process the output of everything Slips need. Manages all the output
    If any Slips module or process needs to output anything to screen, or logs,
    it should use always the output queue. Then this output class will handle how to deal with it
    """

    def __init__(
        self,
        inputqueue,
        verbose,
        debug,
        redis_port,
        stdout='',
        stderr='output/errors.log',
        slips_logfile='output/slips.log'
    ):
        multiprocessing.Process.__init__(self)
        self.verbose = verbose
        self.debug = debug
        ####### create the log files
        self.errors_logfile = stderr
        self.slips_logfile = slips_logfile
        self.name = 'Output'
        self.queue = inputqueue
        self.create_logfile(self.errors_logfile)
        self.create_logfile(self.slips_logfile)
        # self.quiet manages if we should really print stuff or not
        self.quiet = False
        if stdout != '':
            self.change_stdout(stdout)
        if self.verbose > 2:
            print(
                f'Verbosity: {str(self.verbose)}. Debugging: {str(self.debug)}'
            )
        # Start the DB
        __database__.start(redis_port)


    def log_branch_info(self, logfile):
        branch_info = utils.get_branch_info()
        if branch_info:
            # it's false when we're in docker because there's no .git/ there
            commit, branch = branch_info[0], branch_info[1]
            now = datetime.now()
            with open(logfile, 'a') as f:
                f.write(f'Using {branch} - {commit} - {now}\n\n')

    def create_logfile(self, path):
        """
        creates slips.log and errors.log if they don't exist
        """
        try:
            open(path, 'a').close()
        except FileNotFoundError:
            p = Path(os.path.dirname(path))
            p.mkdir(parents=True, exist_ok=True)
            open(path, 'w').close()

        self.log_branch_info(path)


    def log_line(self, sender, msg):
        """
        Log error line to slips.log
        """
        # don't log in daemon mode, all printed
        # lines are redirected to slips.log by default
        if "-D" in sys.argv and 'update'.lower() not in sender and 'stopping' not in sender:
            # if the sender is the update manager, always log
            return

        with open(self.slips_logfile, 'a') as slips_logfile:
            date_time = datetime.now()
            date_time = utils.convert_format(date_time, utils.alerts_format)
            slips_logfile.write(f'{date_time} {sender}{msg}\n')


    def change_stdout(self, file):
        # io.TextIOWrapper creates a file object of this file
        # Pass 0 to open() to switch output buffering off (only allowed in binary mode)
        # write_through= True, to flush the buffer to disk, from there the file can read it.
        # without it, the file writer keeps the information in a local buffer that's not accessible to the file.
        sys.stdout = io.TextIOWrapper(open(file, 'wb', 0), write_through=True)
        return

    def process_line(self, line):
        """
        Extract the verbosity level, the sender and the message from the line.
        The line is separated by | and the fields are:
        1. The level. It means the importance/verbosity we should be. The lower the less important
            The level is a two digit number
            first digit: verbosity level
            second digit: debug level
            both levels range from 0 to 3

            verbosity:
                0 - don't print
                1 - basic operation/proof of work
                2 - log I/O operations and filenames
                3 - log database/profile/timewindow changes

            debug:
                0 - don't print
                1 - print exceptions
                2 - unsupported and unhandled types (cases that may cause errors)
                3 - red warnings that needs examination - developer warnings

            Messages should be about verbosity or debugging, but not both simultaneously
        2. The sender
        3. The message

        The level is always an integer from 0 to 10
        """
        try:
            try:
                level = line.split('|')[0]
                if int(level) < 0 or int(level) >= 100 or len(level) < 2:
                    level = '00'
            except TypeError:
                print('Error in the level sent to the Output Process')
            except KeyError:
                level = '00'
                print(
                    'The level passed to OutputProcess was wrongly formated.'
                )
            except ValueError as inst:
                # We probably received some text instead of an int()
                print(
                    'Error receiving a text to output. '
                    'Check that you are sending the format of the msg correctly: level|msg'
                )
                print(inst)
                sys.exit(-1)

            try:
                sender = f"[{line.split('|')[1]}] "
            except KeyError:
                sender = ''
                print(
                    'The sender passed to OutputProcess was wrongly formatted.'
                )
                sys.exit(-1)

            try:
                # If there are more | inside the msg, we don't care, just print them
                msg = ''.join(line.split('|')[2:])
            except KeyError:
                msg = ''
                print(
                    'The message passed to OutputProcess was wrongly formatted.'
                )
                sys.exit(-1)
            return (level, sender, msg)

        except Exception as inst:
            exception_line = sys.exc_info()[2].tb_lineno
            print(
                f'\tProblem with process line in OutputProcess() line '
                f'{exception_line}'
            )
            print(type(inst))
            print(inst.args)
            print(inst)
            sys.exit(1)

    def log_error(self, sender, msg):
        """
        Log error line to errors.log
        """
        with open(self.errors_logfile, 'a') as errors_logfile:
            date_time = datetime.now()
            date_time = utils.convert_format(date_time, utils.alerts_format)
            errors_logfile.write(f'{date_time} {sender}{msg}\n')

    def output_line(self, level, sender, msg):
        """
        Print depending on the debug and verbose levels
        """
        # (level, sender, msg) = self.process_line(line)
        verbose_level, debug_level = int(level[0]), int(level[1])
        # if verbosity level is 3 make it red
        if debug_level == 3:
            msg = f'\033[0;35;40m{msg}\033[00m'

        # There should be a level 0 that we never print. So its >, and not >=
        if ((
            verbose_level > 0 and verbose_level <= 3
            and verbose_level <= self.verbose
        ) or (
            debug_level > 0 and debug_level <= 3
            and debug_level <= self.debug
        )):
            if 'Start' in msg:
                print(f'{msg}')
                return
            print(f'{sender}{msg}')
            self.log_line(sender, msg)

        # if the line is an error and we're running slips without -e 1 , we should log the error to output/errors.log
        # make sure the msg is an error. debug_level==1 is the one printing errors
        if debug_level == 1:
            self.log_error(sender, msg)

    def shutdown_gracefully(self):
        self.log_line('[Output Process]', ' Stopping output process. '
                                        'Further evidence may be missing. '
                                        'Check alerts.log for full evidence list.')
        __database__.publish('finished_modules', self.name)

    def run(self):


        while True:
            try:
                line = self.queue.get()
                if line == 'quiet':
                    self.quiet = True
                elif 'stop_process' in line or line == 'stop':
                    self.shutdown_gracefully()
                    return True
                elif not self.quiet:
                    # output to terminal and logs or logs only?

                    if 'log-only' in line:
                        line = line.replace('log-only', '')
                        (level, sender, msg) = self.process_line(line)
                        self.log_line(sender, msg)
                    else:
                        (level, sender, msg) = self.process_line(line)
                        # output to terminal
                        self.output_line(level, sender, msg)

                else:
                    # Here we should still print the lines coming in
                    # the input for a while after receiving a 'stop'. We don't know how to do it.
                    print('Stopping the output process')
                    self.shutdown_gracefully()
                    return True

            except KeyboardInterrupt:
                self.shutdown_gracefully()
                return True
            except Exception as inst:
                exception_line = sys.exc_info()[2].tb_lineno
                print(
                    f'\tProblem with OutputProcess() line {exception_line}',
                )
                print(type(inst))
                print(inst.args)
                print(inst)
                print(traceback)
                return True
