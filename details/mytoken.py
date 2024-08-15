#OS is the library which works with operating system
#it gives us many functions to interact with file directories

#dotenv is a library which sets the environemnt variables when a program
#is executed 

#environment variables are the variables which are set outside the source code

import os
from dotenv import load_dotenv

#reads the .env file 
load_dotenv()

#returns with the value of the key passed in the function
#otherwise returns NONE
TOKEN = os.getenv("TOKEN")