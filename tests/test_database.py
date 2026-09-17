import duckdb
from atlas.build import build


def test_database_is_queryable_and_relational(project):
    r = build(project)
    with duckdb.connect(str(project/'data/build/atlas.duckdb'), read_only=True) as con:
        tables = {x[0] for x in con.execute('show tables').fetchall()}
        assert {'claims','gaps','foods','organisms','sources','molecules','nutrients','processes'} <= tables
        assert con.execute('select count(*) from foods').fetchone()[0] == 3
        assert con.execute('select count(*) from claims c left join sources s on c.src=s.id where s.id is null').fetchone()[0] == 0
        assert con.execute('select max(value_numeric) from claims where "group"=\'nutrition\'').fetchone()[0] == 58.0
        assert con.execute('select distinct tier from claims order by tier').fetchall() == [(1,), (2,), (3,), (4,)]
        assert con.execute('select value_numeric from claims where v=\'present\' limit 1').fetchone()[0] is None
