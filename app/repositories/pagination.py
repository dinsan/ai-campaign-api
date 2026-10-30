# Defaults shared by every list endpoint. Clients page through results with
# ``limit``/``offset``; the cap stops a single request from pulling an
# unbounded number of rows.
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
