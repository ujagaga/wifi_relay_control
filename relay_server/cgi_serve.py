#!/usr/bin/env python3

from wsgiref.handlers import CGIHandler
from index import application

CGIHandler().run(application)
