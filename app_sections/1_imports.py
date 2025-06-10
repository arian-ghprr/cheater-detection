# بخش 1: وارد کردن کتابخانه‌ها
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr
import numpy as np
from itertools import combinations
import json
import os
import pandas as pd
from datetime import datetime, timedelta
