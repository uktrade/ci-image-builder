from typing import List


class StubbedProcess:
    _returncode: int
    _returncodes: List[int]
    _returncode_pointer: int

    def __init__(self, returncode=0, returncodes=None, stdout=None):
        self._returncode = returncode
        self._returncodes = returncodes
        self._returncode_pointer = 0
        self.stdout = stdout

    @property
    def returncode(self):
        if self._returncodes is not None:
            if self._returncode_pointer >= len(self._returncodes):
                returncode = self._returncodes[-1]
            else:
                returncode = self._returncodes[self._returncode_pointer]
            self._returncode_pointer += 1
            return returncode

        return self._returncode
