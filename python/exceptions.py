class WerewolfException(Exception):
    pass


class PermissionException(WerewolfException):
    pass


class PersonNotFoundException(WerewolfException):
    pass

class DocumentFoundException(Exception):
    pass