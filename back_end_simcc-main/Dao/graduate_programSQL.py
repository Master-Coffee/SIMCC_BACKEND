import pandas as pd

import Dao.sgbdSQL as sgbdSQL
import Model.GraduateProgram_Production as GraduateProgram_Production

pd.set_option("future.no_silent_downcasting", True)


def graduate_program_db(institution_id):
    reg = sgbdSQL.consultar_db(
        " SELECT graduate_program_id,code,name as program,area,modality,type, rating "
        " FROM graduate_program gp where institution_id='%s'" % institution_id
    )

    df_bd = pd.DataFrame(
        reg,
        columns=[
            "graduate_program_id",
            "code",
            "program",
            "area",
            "modality",
            "type",
            "rating",
        ],
    )

    print(df_bd)

    return df_bd


def graduate_program_profnit_db(graduate_program_id):
    graduate_program_filter = str()
    if graduate_program_id:
        graduate_program_filter = (
            f"""WHERE gp.graduate_program_id = '{graduate_program_id}'"""
        )
    sql = f"""
        SELECT
            gp.graduate_program_id,
            gp.code,
            gp.name,
            gp.area,
            gp.modality,
            gp.type,
            gp.rating,
            gp.institution_id,
            gp.description,
            gp.url_image,
            gp.city,
            gp.visible,
            gp.created_at,
            gp.updated_at,
            COUNT(CASE WHEN gr.type_ = 'PERMANENTE' THEN 1 END) as qtd_permanente,
            COUNT(CASE WHEN gr.type_ = 'COLABORADOR' THEN 1 END) as qtd_colaborador
        FROM
            graduate_program gp
            LEFT JOIN graduate_program_researcher gr ON gp.graduate_program_id = gr.graduate_program_id
            LEFT JOIN graduate_program_student gps ON gps.graduate_program_id = gp.graduate_program_id
        {graduate_program_filter}
        GROUP BY
            gp.graduate_program_id
        """
    registry = sgbdSQL.consultar_db(sql)

    data_frame = pd.DataFrame(
        registry,
        columns=[
            "graduate_program_id",
            "code",
            "name",
            "area",
            "modality",
            "type",
            "rating",
            "institution_id",
            "description",
            "url_image",
            "city",
            "visible",
            "created_at",
            "updated_at",
            "qtd_permanente",
            "qtd_colaborador",
        ],
    )
    script_sql = """
        SELECT
            gp.graduate_program_id,
            COUNT(gps.researcher_id)
        FROM
            graduate_program gp
            LEFT JOIN graduate_program_student gps ON gp.graduate_program_id = gps.graduate_program_id
        GROUP BY
            gp.graduate_program_id
        """

    registry = sgbdSQL.consultar_db(script_sql)

    df = pd.DataFrame(registry, columns=["graduate_program_id", "qtd_student"])

    data_frame = pd.merge(data_frame, df, on="graduate_program_id", how="left")

    data_frame["visible"] = data_frame["visible"].astype("str")

    return data_frame.to_dict(orient="records")

# HERE production_general_db
def production_general_db(graduate_program_id, year, dep_id):
    filter = ""
    if graduate_program_id and graduate_program_id != "0":
        filter = f"AND graduate_program_id = '{graduate_program_id}'"

    if filter != "":
        sql = f"""
            SELECT COUNT(graduate_program_id) AS qtd,
                   'PATENT' AS type,
                   graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM
            patent p, graduate_program_researcher gpr
            WHERE gpr.researcher_id = p.researcher_id {filter} AND p.development_year::int >= {year}
            GROUP BY type, graduate_program_id, gpr.year

            UNION

            SELECT COUNT(graduate_program_id) AS qtd,
                   'SOFTWARE' AS type,
                   graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM software s, graduate_program_researcher gpr
            WHERE gpr.researcher_id = s.researcher_id {filter} AND s.year >= {year}
            GROUP BY graduate_program_id, gpr.year

            UNION

            SELECT COUNT(graduate_program_id) AS qtd,
                   'BRAND' AS type,
                   graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM brand b, graduate_program_researcher gpr
            WHERE gpr.researcher_id = b.researcher_id {filter} AND b.year >= {year}
            GROUP BY graduate_program_id, gpr.year

            UNION

            SELECT COUNT(graduate_program_id) AS qtd,
                   'ARTICLE' AS type,
                   gpr.graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, graduate_program_researcher gpr
            WHERE b.researcher_id = gpr.researcher_id AND TYPE = 'ARTICLE' {filter} AND year_ >= {year}
            GROUP BY TYPE, graduate_program_id, gpr.year

            UNION

            SELECT COUNT(graduate_program_id) AS qtd,
                   'BOOK' AS type,
                   gpr.graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, graduate_program_researcher gpr
            WHERE b.researcher_id = gpr.researcher_id AND TYPE = 'BOOK' {filter} AND year_ >= {year}
            GROUP BY TYPE, graduate_program_id, gpr.year

            UNION

            SELECT COUNT(graduate_program_id) AS qtd,
                   'BOOK_CHAPTER' AS type,
                   gpr.graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, graduate_program_researcher gpr
            WHERE b.researcher_id = gpr.researcher_id AND TYPE = 'BOOK_CHAPTER' {filter} AND year_ >= {year}
            GROUP BY TYPE, graduate_program_id, gpr.year

            UNION

            SELECT COUNT(graduate_program_id) AS qtd,
                   'WORK_IN_EVENT' AS type,
                   gpr.graduate_program_id AS graduate_program_id,
                   gpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, graduate_program_researcher gpr
            WHERE b.researcher_id = gpr.researcher_id AND TYPE = 'WORK_IN_EVENT' {filter} AND year_ >= {year}
            GROUP BY TYPE, graduate_program_id, gpr.year

            UNION

            SELECT
                COUNT(*),
                r.graduation,
                gpr.graduate_program_id,
                NULL as year
            FROM
                researcher r
                RIGHT JOIN graduate_program_researcher gpr ON gpr.researcher_id = r.id 
            WHERE
            1 = 1
            {filter}
            GROUP BY
                r.graduation, gpr.graduate_program_id
            """
    else:
        filter_departament = (
            f"""
            AND researcher_id IN 
            (SELECT researcher_id FROM public.departament_researcher WHERE dep_id = '{dep_id}')
            """
            if dep_id
            else str()
        )

        filter_departament_researcher = (
            f"""
            AND id IN 
            (SELECT researcher_id FROM public.departament_researcher WHERE dep_id = '{dep_id}')
            """
            if dep_id
            else str()
        )

        sql = f"""
            SELECT COUNT(DISTINCT p.title) AS qtd, 'PATENT' AS type
            FROM patent p
            WHERE
                p.development_year::int >= {year}
                {filter_departament}
            GROUP BY type

            UNION

            SELECT COUNT(DISTINCT s.title) AS qtd, 'SOFTWARE' AS TYPE
            FROM software s
            WHERE s.year >= {year}
            {filter_departament}
            GROUP BY TYPE

            UNION

            SELECT COUNT(DISTINCT b.title) AS qtd, 'BRAND' AS TYPE
            FROM brand b
            WHERE b.year >= {year}
            {filter_departament}
            GROUP BY TYPE

            UNION

            SELECT COUNT(DISTINCT b.title) AS qtd, 'ARTICLE' AS TYPE
            FROM PUBLIC.bibliographic_production b
            WHERE TYPE = 'ARTICLE' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE

            UNION

            SELECT COUNT(DISTINCT b.title) AS qtd, 'BOOK' AS TYPE
            FROM PUBLIC.bibliographic_production b
            WHERE TYPE = 'BOOK' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE

            UNION

            SELECT COUNT(DISTINCT b.title) AS qtd, 'BOOK_CHAPTER' AS TYPE
            FROM PUBLIC.bibliographic_production b
            WHERE TYPE = 'BOOK_CHAPTER' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE

            UNION

            SELECT COUNT(DISTINCT b.title) AS qtd, 'WORK_IN_EVENT' AS TYPE
            FROM PUBLIC.bibliographic_production b
            WHERE TYPE = 'WORK_IN_EVENT' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE

            UNION

            SELECT COUNT(*) as qtd, UPPER(r.graduation)
            FROM researcher r
            WHERE 
            1 = 1
            AND r.id NOT IN (SELECT researcher_id FROM graduate_program_student)
            {filter_departament_researcher[3:]}
            GROUP BY graduation
            """
    reg = sgbdSQL.consultar_db(sql)

    if filter != "":
        df_bd = pd.DataFrame(
            reg, columns=["qtd", "tipo", "graduate_program_id", "year"]
        )
    else:
        df_bd = pd.DataFrame(reg, columns=["qtd", "tipo"])

    list_graduateProgram_Production = []
    graduateProgram_Production_ = (
        GraduateProgram_Production.GraduateProgram_Production()
    )

    graduateProgram_Production_.id = graduate_program_id
    for i, infos in df_bd.iterrows():
        if infos.tipo == "BOOK":
            graduateProgram_Production_.book = infos.qtd
        if infos.tipo == "WORK_IN_EVENT":
            graduateProgram_Production_.work_in_event = infos.qtd
        if infos.tipo == "ARTICLE":
            graduateProgram_Production_.article = infos.qtd
        if infos.tipo == "BOOK_CHAPTER":
            graduateProgram_Production_.book_chapter = infos.qtd
        if infos.tipo == "PATENT":
            graduateProgram_Production_.patent = infos.qtd
        if infos.tipo == "SOFTWARE":
            graduateProgram_Production_.software = infos.qtd
        if infos.tipo == "BRAND":
            graduateProgram_Production_.brand = infos.qtd
        if infos.tipo == "DOUTORADO":
            graduateProgram_Production_.doctors = infos.qtd
        if infos.tipo == "MESTRADO":
            graduateProgram_Production_.masters = infos.qtd
        if infos.tipo == "GRADUAÇÃO":
            graduateProgram_Production_.graduate = infos.qtd
        if infos.tipo == "ESPECIALIZAÇÃO":
            graduateProgram_Production_.specialization = infos.qtd
        if infos.tipo == "PÓS-DOUTORADO":
            graduateProgram_Production_.pos_doctors = infos.qtd

    if filter != "":
        sql = f"""
            SELECT COUNT(*) AS qtd
            FROM graduate_program_researcher gpr
            WHERE graduate_program_id = '{graduate_program_id}'
            """
    else:
        sql = """
            SELECT COUNT(*) AS qtd
            FROM researcher r"""

    reg = sgbdSQL.consultar_db(sql)
    df_bd = pd.DataFrame(reg, columns=["qtd"])
    for i, infos in df_bd.iterrows():
        graduateProgram_Production_.researcher = str(infos.qtd)

    list_graduateProgram_Production.append(graduateProgram_Production_.getJson())

    list_graduateProgram_Production = pd.DataFrame(list_graduateProgram_Production)

    return list_graduateProgram_Production.replace("", 0).to_dict(orient="records")
# . . . . . . . . . . . . . . . . . . 





# ● incite_production_general_db
def incite_production_general_db(graduate_program_id, _year, _dep_id):

    INCITE_program_id = graduate_program_id
    year = "1900"
    dep_id = ""

    filter = ""
    if INCITE_program_id and INCITE_program_id != "0":
        filter = f"AND incite_graduate_program_id = '{INCITE_program_id}'"

    if filter != "":

        sql = f"""
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'PATENT' AS type,
                    incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM
            patent p, incite_graduate_program_researcher igpr
            WHERE igpr.researcher_id = p.researcher_id {filter} AND p.development_year::int >= {year}
            GROUP BY type, incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'SOFTWARE' AS type,
                    incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM software s, incite_graduate_program_researcher igpr
            WHERE igpr.researcher_id = s.researcher_id {filter} AND s.year >= {year}
            GROUP BY incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'BRAND' AS type,
                    incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM brand b, incite_graduate_program_researcher igpr
            WHERE igpr.researcher_id = b.researcher_id {filter} AND b.year >= {year}
            GROUP BY incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'ARTICLE' AS type,
                    igpr.incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, incite_graduate_program_researcher igpr
            WHERE b.researcher_id = igpr.researcher_id AND TYPE = 'ARTICLE' {filter} AND year_ >= {year}
            GROUP BY TYPE, incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'BOOK' AS type,
                    igpr.incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, incite_graduate_program_researcher igpr
            WHERE b.researcher_id = igpr.researcher_id AND TYPE = 'BOOK' {filter} AND year_ >= {year}
            GROUP BY TYPE, incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'BOOK_CHAPTER' AS type,
                    igpr.incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, incite_graduate_program_researcher igpr
            WHERE b.researcher_id = igpr.researcher_id AND TYPE = 'BOOK_CHAPTER' {filter} AND year_ >= {year}
            GROUP BY TYPE, incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT COUNT(incite_graduate_program_id) AS qtd,
                    'WORK_IN_EVENT' AS type,
                    igpr.incite_graduate_program_id AS incite_graduate_program_id,
                    igpr.year AS year_pos
            FROM PUBLIC.bibliographic_production b, incite_graduate_program_researcher igpr
            WHERE b.researcher_id = igpr.researcher_id AND TYPE = 'WORK_IN_EVENT' {filter} AND year_ >= {year}
            GROUP BY TYPE, incite_graduate_program_id, igpr.year
    
            UNION
    
            SELECT
                COUNT(*) as qtd,
                UPPER(r.graduation) as type,
                igpr.incite_graduate_program_id,
                0000 as year
            FROM
                researcher r
                LEFT JOIN incite_graduate_program_researcher igpr ON igpr.researcher_id = r.id
                WHERE year >= {year} {filter}
            GROUP BY graduation, igpr.incite_graduate_program_id
            """
    else:
        if dep_id:

            # WARN NO departament_researcher table

            filter_departament = f"""AND r.id IN (
                    SELECT researcher_id
                    FROM public.departament_researcher
                    WHERE dep_id = '{dep_id}'
                )
                """
        else:
            filter_departament = str()


        sql = f"""
            SELECT COUNT(r.id) AS qtd, 'PATENT' AS type
            FROM patent p, researcher r
            WHERE
                r.id = p.researcher_id
                AND p.development_year::int >= {year}
                {filter_departament}
            GROUP BY type
    
            UNION
    
            SELECT COUNT(r.id) AS qtd, 'SOFTWARE' AS TYPE
            FROM software s, researcher r
            WHERE r.id = s.researcher_id AND s.year >= {year}
            {filter_departament}
            GROUP BY TYPE
    
            UNION
    
            SELECT COUNT(r.id) AS qtd, 'BRAND' AS TYPE
            FROM brand b, researcher r
            WHERE r.id = b.researcher_id AND b.year >= {year}
            {filter_departament}
            GROUP BY TYPE
    
            UNION
    
            SELECT COUNT(r.id) AS qtd, 'ARTICLE' AS TYPE
            FROM PUBLIC.bibliographic_production b, researcher r
            WHERE b.researcher_id = r.id AND TYPE = 'ARTICLE' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE
    
            UNION
    
            SELECT COUNT(r.id) AS qtd, 'BOOK' AS TYPE
            FROM PUBLIC.bibliographic_production b, researcher r
            WHERE b.researcher_id = r.id AND TYPE = 'BOOK' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE
    
            UNION
    
            SELECT COUNT(r.id) AS qtd, 'BOOK_CHAPTER' AS TYPE
            FROM PUBLIC.bibliographic_production b, researcher r
            WHERE b.researcher_id = r.id AND TYPE = 'BOOK_CHAPTER' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE
    
            UNION
    
            SELECT COUNT(r.id) AS qtd, 'WORK_IN_EVENT' AS TYPE
            FROM PUBLIC.bibliographic_production b, researcher r
            WHERE b.researcher_id = r.id AND TYPE = 'WORK_IN_EVENT' AND year_ >= {year}
            {filter_departament}
            GROUP BY TYPE
    
            UNION
    
            SELECT COUNT(*) as qtd, UPPER(r.graduation)
            FROM researcher r 
            {f'WHERE {filter_departament[3:]}' if filter_departament else str()}
            GROUP BY graduation
            """

    reg = sgbdSQL.consultar_db(sql)

    if filter != "":
        df_bd = pd.DataFrame(
            reg, columns=["qtd", "tipo", "incite_graduate_program_id", "year"]
        )
    else:
        df_bd = pd.DataFrame(reg, columns=["qtd", "tipo"])

    list_graduateProgram_Production = []

    graduateProgram_Production_ = (
        GraduateProgram_Production.GraduateProgram_Production()
    )

    graduateProgram_Production_.id = INCITE_program_id
    for i, infos in df_bd.iterrows():
        if infos.tipo == "BOOK":
            graduateProgram_Production_.book = infos.qtd
        if infos.tipo == "WORK_IN_EVENT":
            graduateProgram_Production_.work_in_event = infos.qtd
        if infos.tipo == "ARTICLE":
            graduateProgram_Production_.article = infos.qtd
        if infos.tipo == "BOOK_CHAPTER":
            graduateProgram_Production_.book_chapter = infos.qtd
        if infos.tipo == "PATENT":
            graduateProgram_Production_.patent = infos.qtd
        if infos.tipo == "SOFTWARE":
            graduateProgram_Production_.software = infos.qtd
        if infos.tipo == "BRAND":
            graduateProgram_Production_.brand = infos.qtd
        if infos.tipo == "DOUTORADO":
            graduateProgram_Production_.doctors = infos.qtd
        if infos.tipo == "MESTRADO":
            graduateProgram_Production_.masters = infos.qtd
        if infos.tipo == "GRADUAÇÃO":
            graduateProgram_Production_.graduate = infos.qtd
        if infos.tipo == "ESPECIALIZAÇÃO":
            graduateProgram_Production_.specialization = infos.qtd
        if infos.tipo == "PÓS-DOUTORADO":
            graduateProgram_Production_.pos_doctors = infos.qtd

    if filter != "":
        sql = f"""
            SELECT COUNT(*) AS qtd
            FROM incite_graduate_program_researcher igpr
            WHERE incite_graduate_program_id = '{INCITE_program_id}'
            """
    else:
        sql = """
            SELECT COUNT(*) AS qtd
            FROM researcher r"""

    reg = sgbdSQL.consultar_db(sql)
    df_bd = pd.DataFrame(reg, columns=["qtd"])
    for i, infos in df_bd.iterrows():
        graduateProgram_Production_.researcher = str(infos.qtd)

    list_graduateProgram_Production.append(graduateProgram_Production_.getJson())

    list_graduateProgram_Production = pd.DataFrame(list_graduateProgram_Production)

    return list_graduateProgram_Production.replace("", 0).to_dict(orient="records")

# . . . . . . . . . . . . . . . . . . 





# ● incite_program_profnit_db
def incite_program_profnit_db(program_id):
    program_filter = str()
    if program_id:
        program_filter = f"""WHERE igp.incite_graduate_program_id = '{program_id}'"""
    sql = f"""
        SELECT
            igp.incite_graduate_program_id,
            igp.name,
            igp.description,
            igp.link,
            igp.institution_id,
            igp.created_at,
            igp.updated_at,
            igp.visible,
            COUNT(*) as qtd_researcher
        FROM
            incite_graduate_program igp
            LEFT JOIN incite_graduate_program_researcher igr ON igp.incite_graduate_program_id = igr.incite_graduate_program_id
        {program_filter}
        GROUP BY
            igp.incite_graduate_program_id
        """
    registry = sgbdSQL.consultar_db(sql)

    data_frame = pd.DataFrame(
        registry,
        columns=[
            "incite_graduate_program_id",
            "name",
            "description",
            "link",
            "institution_id",
            "created_at",
            "updated_at",
            "visible",
            "qtd_researcher",
        ],
    )

    data_frame["visible"] = data_frame["visible"].astype("str")

    return data_frame.to_dict(orient="records")
# . . . . . . . . . . . . . . . . . . 
