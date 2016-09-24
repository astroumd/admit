""" .. _admitloggingapi:

   **logging** --- Message logging functionality.
   ----------------------------------------------

   This module implements the ADMIT logging infrastructure.
"""
import logging
from inspect import stack, getargvalues
import sys
import copy


class AdmitLogging(object):
    """ This is effectively a static class for the logging in ADMIT.
        It relies on the Python logging module and has the same logging
        calls as that module but also offers header and subheader methods
        which allow for annotation in the log.

        Parameters
        ----------
        None

        Attributes
        ----------
        None

    """
    #  if you add some new items here, be sure to add the associated string in
    #  Admit.py where e.g.  logging.addLevelName(logging.TIMING,"TIMING")
    TIMING     = 15                  # new one for ADMIT
    REGRESSION = 21                  # new one for ADMIT
    CRITICAL   = logging.CRITICAL    # 50
    ERROR      = logging.ERROR       # 40
    WARNING    = logging.WARNING     # 30
    INFO       = logging.INFO        # 20
    DEBUG      = logging.DEBUG       # 10
    loggers = set()             # set of the names of all registered loggers
    EFFECTIVELOGLEVEL = 20      # all loggers must have the same level

    @staticmethod
    def init(name, logfile, level):
        """ Method to initialize a new named logger

            Parameters
            ----------
            name : str
                Unique name of the logger

            logfile : str
                Full path to the log file to generate

            level : int
                The initial logging level to set. All messages
                at or above this level will be emitted.

            Returns
            -------
            None

        """
        # if the logger is already registered then just return
        if name in AdmitLogging.loggers:
            return
        # create a new named logger, set up the handlers, log levels
        logger = logging.getLogger(name)
        AdmitLogging.EFFECTIVELOGLEVEL = level
        logger.setLevel(level)
        fmt = "%(levelname)s : %(message)s"
        try:
            fhandler = logging.FileHandler(logfile)
            fhandler.setFormatter(logging.Formatter(fmt))
            fhandler.setLevel(level)
            logger.addHandler(fhandler)
        except Exception, msg:
            print "WARNING"
            print "WARNING   Cannot write to log file: %s" % (msg)
            print "WARNING   File logging disabled, logging will only appear on screen."
            print "WARNING"
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
        # add the logger name to the set
        AdmitLogging.loggers.add(name)

    @staticmethod
    def warning(message):
        """ Method to emit a warning level message to the log(s)

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        caller_frame = stack()[1]
        fl = caller_frame[0].f_globals.get('__file__', None)
        # pare down the file name so that it is just .py not .pyc
        if fl.endswith("yc"):
            msg = fl[fl.rfind("/") + 1:-1] + " : " + message
        else:
            msg = fl[fl.rfind("/") + 1:] + " : " + message
        # if there is no logger then just print to the screen
        if logger is None:
            print "WARNING : " + msg
        else:
            logger.warning(msg)

    @staticmethod
    def info(message):
        """ Method to emit an info level message to the log(s)

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        caller_frame = stack()[1]
        fl = caller_frame[0].f_globals.get('__file__', None)
        # pare down the file name so that it is just .py not .pyc
        if fl.endswith("yc"):
            msg = fl[fl.rfind("/") + 1:-1] + " : " + message
        else:
            msg = fl[fl.rfind("/") + 1:] + " : " + message
        # if there is no logger then just print to the screen
        if logger is None:
            print "INFO : " + msg
        else:
            logger.info(msg)


    @staticmethod
    def error(message):
        """ Method to emit an error level message to the log(s)

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        caller_frame = stack()[1]
        fl = caller_frame[0].f_globals.get('__file__', None)
        # pare down the file name so that it is just .py not .pyc
        if fl.endswith("yc"):
            msg = fl[fl.rfind("/") + 1:-1] + " : " + message
        else:
            msg = fl[fl.rfind("/") + 1:] + " : " + message
        # if there is no logger then just print to the screen
        if logger is None:
            print "ERROR : " + msg
        else:
            logger.error(msg)

    @staticmethod
    def critical(message):
        """ Method to emit a critial level message to the log(s)

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        caller_frame = stack()[1]
        fl = caller_frame[0].f_globals.get('__file__', None)
        # pare down the file name so that it is just .py not .pyc
        if fl.endswith("yc"):
            msg = fl[fl.rfind("/") + 1:-1] + " : " + message
        else:
            msg = fl[fl.rfind("/") + 1:] + " : " + message
        # if there is no logger then just print to the screen
        if logger is None:
            print "CRITICAL : " + msg
        else:
            logger.critical(msg)

    @staticmethod
    def debug(message):
        """ Method to emit a debug level message to the log(s)

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        caller_frame = stack()[1]
        fl = caller_frame[0].f_globals.get('__file__', None)
        # pare down the file name so that it is just .py not .pyc
        if fl.endswith("yc"):
            msg = fl[fl.rfind("/") + 1:-1] + " : " + message
        else:
            msg = fl[fl.rfind("/") + 1:] + " : " + message
        # if there is no logger then just print to the screen
        if logger is None:
            print "DEBUG : " + msg
        else:
            logger.debug(msg)

    @staticmethod
    def log(level, message):
        """ Method to emit a log message to the log(s) at the given level

            Parameters
            ----------
            level : int
                The logging level to send the message at

            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        caller_frame = stack()[1]
        fl = caller_frame[0].f_globals.get('__file__', None)
        # pare down the file name so that it is just .py not .pyc
        if fl.endswith("yc"):
            msg = fl[fl.rfind("/") + 1:-1] + " : " + message
        else:
            msg = fl[fl.rfind("/") + 1:] + " : " + message
        # if there is no logger then just print to the screen
        if logger is None:
            print "LOG : " + msg
        else:
            logger.log(level, msg)

    @staticmethod
    def timing(message):
        """ Method to emit a timing message to the log(s)

            Parameters
            ----------
            message : str
                The message to send to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        if logger is None:
            return
        logger.log(AdmitLogging.TIMING, message)

    @staticmethod
    def regression(message):
        """ Method to emit a regression message to the log(s)

            It is suggested to start the message with a magic word followed
            by a colon, so top level scripts can reliably parse them. It is
            typically not needed to add verbosely what these numbers are,
            just the numbers are fine, the associated label defines them
            elsewhere. An example of use:

            logging.regression('CUBEFLUX: %g %g' % (flux1,flux2))

            Parameters
            ----------
            message : str
                The message to send to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        if logger is None:
            return
        logger.log(AdmitLogging.REGRESSION, message)

    @staticmethod
    def findLogger():
        """ Method to get the appropriate logger. This is done by inspecting
            the stack, looking for either Admit.py or AT.py, both of which
            have the name of their loggers.

            Parameters
            ----------
            None

            Returns
            -------
            Instance of the logger (or None)

        """
        aclass = None
        for i in stack():
            # look for either AT.py or Admit.py in the stack
            if "Admit.py" in i[1] or "AT.py" in i[1]:
                # when found, get the class instance
                for k in getargvalues(i[0]).locals.keys():
                    if 'self' == k:
                        aclass = getargvalues(i[0]).locals[k]
                        break
        # if there is none found, or the found name is not registered
        if aclass is None or not hasattr(aclass,"_loggername") or aclass._loggername not in AdmitLogging.loggers:
            # if there is only 1 registered logger then go with that one
            if len(AdmitLogging.loggers) == 1:
                return logging.getLogger(next(iter(AdmitLogging.loggers)))
            return None
        return logging.getLogger(aclass._loggername)

    @staticmethod
    def heading(message):
        """ Method to emit a header message to the log(s). Header messages
            are encapsulated in empty lines for emphasis

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        if logger is None:
            return
        logger.info("")
        logger.info("")
        logger.info("   " + message)
        logger.info("")
        logger.info("")

    @staticmethod
    def subheading(message):
        """ Method to emit a subheader message to the log(s). Subheader messages
            are encapsulated in an empty line for emphasis

            Parameters
            ----------
            message : str
                The message to sed to the log

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        if logger is None:
            return
        logger.info("")
        logger.info("   " + message)
        logger.info("")

    @staticmethod
    def reportKeywords(kw):
        """ Method to emit logging messages that report the current state of the
            AT keywords.

            Parameters
            ----------
            kw : dict
                A dictionary containing the AT _keys dictionary

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()        
        if logger is None:
            return
        logger.info("  Run using the following settings:")
        for k, v in kw.iteritems():
            logger.info("    %s :  %s" % (k, str(v)))
        logger.info("")

    @staticmethod
    def addLevelName(level,levelName):
        """ Method to add a new level to the logging schema

            Parameters
            ----------
            level : int
                The level number to add

            levelName : str
                The name to use for the level

            Returns
            -------
            None
        """
        logging.addLevelName(level,levelName)

    @staticmethod
    def basicConfig(**kwargs):
        """ Method to initialize the basic logging module

            Parameters
            ----------
            various

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        if logger is None:
            return
        logger.basicConfig(**kwargs)

    @staticmethod
    def StreamHandler(stream=None):
        """ Method to get a streamhandler object

            Parameters
            ----------
            stream : stream
                The output stream to attache to the stream handler

            Returns
            -------
            Handler object
        """
        return logging.StreamHandler(stream)

    @staticmethod
    def addHandler(handler):
        """ Method to add a handler to the logger

            Parameters
            ----------
            handler : handle to a handler
                The handler to add

            Returns
            -------
            None

        """
        # get the appropriate logger
        logger = AdmitLogging.findLogger()
        if logger is None:
            return
        logger.addHandler(handler)

    @staticmethod
    def Formatter(fmt=None, datefmt=None):
        """ Method to set the format of the logging messages

            Parameters
            ----------
            fmt : str
                The format of the messages

            datefmt : str
                The format for any dates in the log

            Returns
            -------
            Handle to the format object

        """
        return logging.Formatter(fmt, datefmt)

    @staticmethod
    def getEffectiveLevel():
        """ Method to get the current minimum logging level

            Parameters
            ----------
            None

            Returns
            -------
            int continaing the current minimum logging level

        """
        return AdmitLogging.EFFECTIVELOGLEVEL

    @staticmethod
    def setLevel(level):
        """ Method to set the current minimum level that will be logged
            all messages below this level are ignored.

            Parameters
            ----------
            level : int
                The numeric level number to set

            Returns
            -------
            None

        """
        # ensure that all registered loggers have the same level
        AdmitLogging.EFFECTIVELOGLEVEL = level
        for log in AdmitLogging.loggers:
            logger = logging.getLogger(log)
            logger.setLevel(level)

    @staticmethod
    def shutdown():
        """ Method to shuitdown the logging system

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        logging.shutdown()
