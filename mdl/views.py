from django.shortcuts import render
from django.db import connection


def _query(sql, params=()):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _sort_urls(request, fields, sort, dir_):
    urls = {}
    for f in fields:
        p = request.GET.copy()
        p['sort'] = f
        p['dir'] = 'desc' if sort == f and dir_ == 'asc' else 'asc'
        urls[f] = '?' + p.urlencode()
    return urls


# ------------------------------------------------------------------ TABLAS
def tablas(request):
    catalogo = request.GET.get('catalogo', '').strip()
    esquema  = request.GET.get('esquema',  'public').strip()
    tabla    = request.GET.get('tabla',    '').strip()
    sort     = request.GET.get('sort',     'table_name')
    dir_     = request.GET.get('dir',      'asc')

    valid = {'table_catalog', 'table_schema', 'table_name', 'table_type'}
    if sort not in valid:
        sort = 'table_name'
    dir_sql = 'ASC' if dir_ == 'asc' else 'DESC'

    sql = ('SELECT table_catalog, table_schema, table_name, table_type'
           ' FROM information_schema.tables WHERE 1=1')
    params = []
    if esquema:
        sql += ' AND table_schema = %s';    params.append(esquema)
    if catalogo:
        sql += ' AND table_catalog = %s';   params.append(catalogo)
    if tabla:
        sql += ' AND table_name LIKE %s';   params.append(f'%{tabla}%')
    sql += f' ORDER BY {sort} {dir_sql}'

    rows   = _query(sql, params)
    fields = ['table_catalog', 'table_schema', 'table_name', 'table_type']

    return render(request, 'mdl/tablas.html', {
        'rows':      rows,
        'catalogo':  catalogo,
        'esquema':   esquema,
        'tabla':     tabla,
        'sort':      sort,
        'dir':       dir_,
        'surls':     _sort_urls(request, fields, sort, dir_),
    })


# ------------------------------------------------------------------ COLUMNAS
def columnas(request):
    catalogo = request.GET.get('catalogo', '').strip()
    esquema  = request.GET.get('esquema',  'public').strip()
    tabla    = request.GET.get('tabla',    '').strip()
    columna  = request.GET.get('columna',  '').strip()
    sort     = request.GET.get('sort',     'table_name')
    dir_     = request.GET.get('dir',      'asc')

    valid = {'table_catalog', 'table_schema', 'table_name', 'column_name',
             'data_type', 'is_nullable', 'numeric_precision', 'numeric_scale'}
    if sort not in valid:
        sort = 'table_name'
    dir_sql = 'ASC' if dir_ == 'asc' else 'DESC'

    sql = ('SELECT table_catalog, table_schema, table_name, column_name,'
           ' data_type, is_nullable, numeric_precision, numeric_scale'
           ' FROM information_schema.columns WHERE 1=1')
    params = []
    if esquema:
        sql += ' AND table_schema = %s';    params.append(esquema)
    if catalogo:
        sql += ' AND table_catalog = %s';   params.append(catalogo)
    if tabla:
        sql += ' AND table_name LIKE %s';   params.append(f'%{tabla}%')
    if columna:
        sql += ' AND column_name LIKE %s';  params.append(f'%{columna}%')
    sql += f' ORDER BY {sort} {dir_sql}'

    rows   = _query(sql, params)
    fields = ['table_catalog', 'table_schema', 'table_name', 'column_name',
              'data_type', 'is_nullable', 'numeric_precision', 'numeric_scale']

    return render(request, 'mdl/columnas.html', {
        'rows':     rows,
        'catalogo': catalogo,
        'esquema':  esquema,
        'tabla':    tabla,
        'columna':  columna,
        'sort':     sort,
        'dir':      dir_,
        'surls':    _sort_urls(request, fields, sort, dir_),
    })


# ------------------------------------------------------------------ INDICES
def indices(request):
    esquema = request.GET.get('esquema', 'public').strip()
    tabla   = request.GET.get('tabla',   '').strip()
    indice  = request.GET.get('indice',  '').strip()
    sort    = request.GET.get('sort',    'table_name')
    dir_    = request.GET.get('dir',     'asc')

    valid = {'table_name', 'index_name', 'column_name', 'is_primary', 'is_unique', 'index_type'}
    if sort not in valid:
        sort = 'table_name'
    dir_sql = 'ASC' if dir_ == 'asc' else 'DESC'

    sql = '''
        SELECT t.relname  AS table_name,
               i.relname  AS index_name,
               a.attname  AS column_name,
               ix.indisprimary AS is_primary,
               ix.indisunique  AS is_unique,
               am.amname  AS index_type
          FROM pg_class t
          JOIN pg_index     ix ON t.oid = ix.indrelid
          JOIN pg_class     i  ON i.oid = ix.indexrelid
          JOIN pg_attribute a  ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
          JOIN pg_namespace n  ON n.oid = t.relnamespace
          JOIN pg_am        am ON am.oid = i.relam
         WHERE n.nspname = %s
    '''
    params = [esquema or 'public']
    if tabla:
        sql += ' AND t.relname LIKE %s';  params.append(f'%{tabla}%')
    if indice:
        sql += ' AND i.relname LIKE %s';  params.append(f'%{indice}%')
    sql += f' ORDER BY {sort} {dir_sql}'

    rows   = _query(sql, params)
    fields = ['table_name', 'index_name', 'column_name', 'is_primary', 'is_unique', 'index_type']

    return render(request, 'mdl/indices.html', {
        'rows':    rows,
        'esquema': esquema,
        'tabla':   tabla,
        'indice':  indice,
        'sort':    sort,
        'dir':     dir_,
        'surls':   _sort_urls(request, fields, sort, dir_),
    })
