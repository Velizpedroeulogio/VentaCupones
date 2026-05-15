from django.shortcuts import render
from django.db import connection

_OPS = {'eq', 'ne', 'ct', 'nc'}


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


def _op(request, name):
    v = request.GET.get(name, 'ct').strip()
    return v if v in _OPS else 'ct'


def _filter(sql, params, col, value, op):
    if not value:
        return sql, params
    if op == 'eq':
        sql += f' AND {col} = %s';          params.append(value)
    elif op == 'ne':
        sql += f' AND {col} <> %s';         params.append(value)
    elif op == 'nc':
        sql += f' AND {col} NOT LIKE %s';   params.append(f'%{value}%')
    else:
        sql += f' AND {col} LIKE %s';       params.append(f'%{value}%')
    return sql, params


# ------------------------------------------------------------------ TABLAS
def tablas(request):
    catalogo    = request.GET.get('catalogo', '').strip()
    esquema     = request.GET.get('esquema',  'public').strip()
    tabla       = request.GET.get('tabla',    '').strip()
    catalogo_op = _op(request, 'catalogo_op')
    esquema_op  = _op(request, 'esquema_op')
    tabla_op    = _op(request, 'tabla_op')
    sort        = request.GET.get('sort', 'table_name')
    dir_        = request.GET.get('dir',  'asc')

    valid = {'table_catalog', 'table_schema', 'table_name', 'table_type'}
    if sort not in valid:
        sort = 'table_name'
    dir_sql = 'ASC' if dir_ == 'asc' else 'DESC'

    sql = ('SELECT table_catalog, table_schema, table_name, table_type'
           ' FROM information_schema.tables WHERE 1=1')
    params = []
    sql, params = _filter(sql, params, 'table_schema',  esquema,  esquema_op)
    sql, params = _filter(sql, params, 'table_catalog', catalogo, catalogo_op)
    sql, params = _filter(sql, params, 'table_name',    tabla,    tabla_op)
    sql += f' ORDER BY {sort} {dir_sql}'

    fields = ['table_catalog', 'table_schema', 'table_name', 'table_type']
    return render(request, 'mdl/tablas.html', {
        'rows':        _query(sql, params),
        'catalogo':    catalogo,    'catalogo_op': catalogo_op,
        'esquema':     esquema,     'esquema_op':  esquema_op,
        'tabla':       tabla,       'tabla_op':    tabla_op,
        'sort': sort, 'dir': dir_,
        'surls': _sort_urls(request, fields, sort, dir_),
    })


# ------------------------------------------------------------------ COLUMNAS
def columnas(request):
    catalogo    = request.GET.get('catalogo', '').strip()
    esquema     = request.GET.get('esquema',  'public').strip()
    tabla       = request.GET.get('tabla',    '').strip()
    columna     = request.GET.get('columna',  '').strip()
    catalogo_op = _op(request, 'catalogo_op')
    esquema_op  = _op(request, 'esquema_op')
    tabla_op    = _op(request, 'tabla_op')
    columna_op  = _op(request, 'columna_op')
    sort        = request.GET.get('sort', 'table_name')
    dir_        = request.GET.get('dir',  'asc')

    valid = {'table_catalog', 'table_schema', 'table_name', 'column_name',
             'data_type', 'is_nullable', 'numeric_precision', 'numeric_scale'}
    if sort not in valid:
        sort = 'table_name'
    dir_sql = 'ASC' if dir_ == 'asc' else 'DESC'

    sql = ('SELECT table_catalog, table_schema, table_name, column_name,'
           ' data_type, is_nullable, numeric_precision, numeric_scale'
           ' FROM information_schema.columns WHERE 1=1')
    params = []
    sql, params = _filter(sql, params, 'table_schema',  esquema,  esquema_op)
    sql, params = _filter(sql, params, 'table_catalog', catalogo, catalogo_op)
    sql, params = _filter(sql, params, 'table_name',    tabla,    tabla_op)
    sql, params = _filter(sql, params, 'column_name',   columna,  columna_op)
    sql += f' ORDER BY {sort} {dir_sql}'

    fields = ['table_catalog', 'table_schema', 'table_name', 'column_name',
              'data_type', 'is_nullable', 'numeric_precision', 'numeric_scale']
    return render(request, 'mdl/columnas.html', {
        'rows':        _query(sql, params),
        'catalogo':    catalogo,    'catalogo_op': catalogo_op,
        'esquema':     esquema,     'esquema_op':  esquema_op,
        'tabla':       tabla,       'tabla_op':    tabla_op,
        'columna':     columna,     'columna_op':  columna_op,
        'sort': sort, 'dir': dir_,
        'surls': _sort_urls(request, fields, sort, dir_),
    })


# ------------------------------------------------------------------ INDICES
def indices(request):
    esquema    = request.GET.get('esquema', 'public').strip()
    tabla      = request.GET.get('tabla',   '').strip()
    indice     = request.GET.get('indice',  '').strip()
    esquema_op = _op(request, 'esquema_op')
    tabla_op   = _op(request, 'tabla_op')
    indice_op  = _op(request, 'indice_op')
    sort       = request.GET.get('sort', 'table_name')
    dir_       = request.GET.get('dir',  'asc')

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
         WHERE 1=1
    '''
    params = []

    # esquema siempre exact para pg_namespace
    if esquema:
        sql += ' AND n.nspname = %s'; params.append(esquema)

    if tabla:
        op = tabla_op
        if op == 'eq':   sql += ' AND t.relname = %s';          params.append(tabla)
        elif op == 'ne': sql += ' AND t.relname <> %s';         params.append(tabla)
        elif op == 'nc': sql += ' AND t.relname NOT LIKE %s';   params.append(f'%{tabla}%')
        else:            sql += ' AND t.relname LIKE %s';       params.append(f'%{tabla}%')

    if indice:
        op = indice_op
        if op == 'eq':   sql += ' AND i.relname = %s';          params.append(indice)
        elif op == 'ne': sql += ' AND i.relname <> %s';         params.append(indice)
        elif op == 'nc': sql += ' AND i.relname NOT LIKE %s';   params.append(f'%{indice}%')
        else:            sql += ' AND i.relname LIKE %s';       params.append(f'%{indice}%')

    sql += f' ORDER BY {sort} {dir_sql}'

    fields = ['table_name', 'index_name', 'column_name', 'is_primary', 'is_unique', 'index_type']
    return render(request, 'mdl/indices.html', {
        'rows':      _query(sql, params),
        'esquema':   esquema,   'esquema_op': esquema_op,
        'tabla':     tabla,     'tabla_op':   tabla_op,
        'indice':    indice,    'indice_op':  indice_op,
        'sort': sort, 'dir': dir_,
        'surls': _sort_urls(request, fields, sort, dir_),
    })
