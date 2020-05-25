from flask import escape

class Utility:
    def str_sanitize(string):
        return escape(string.strip())