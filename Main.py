import Tkinter as tk
from ApplicationLayout import *


class Main():
    def __init__(self, *args, **kwargs):
        applicationLayout = ApplicationLayout()
        applicationLayout.mainloop()

if __name__ == '__main__':
    Main()