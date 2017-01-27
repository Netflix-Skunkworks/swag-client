import logging
from marshmallow import ValidationError


def format_errors(errors):
    for top_level_name, top_level_dict in errors.items():
        logging.error("Errors in Top-Level Key: {}".format(top_level_name))
        for num, element_errors in top_level_dict.items():
            logging.error("Errors in element# {}".format(num))
            for badkey, problems in element_errors.items():
                logging.error("  key in error: {}".format(badkey))
                for problem in problems:
                    logging.error("    {}".format(problem))


class InvalidSWAGDataException(ValidationError):
    def __init__(self, errors):
        format_errors(errors)

