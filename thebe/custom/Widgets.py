from nevow import stan, tags

def autoTable(headers, rows):
    table = tags.table[
        tags.thead[
            tags.tr[
                [tags.th[i] for i in headers]
            ]
        ],
        tags.tbody[
            [ tags.tr[ [tags.td(valign='top')[i] for i in cols] ] for cols in rows]
        ]
    ]
    return table
