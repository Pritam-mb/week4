import sqlite3, json
con = sqlite3.connect('D:\\week4\\graveyard.db')
cur = con.cursor()
cur.execute('SELECT slug,name,cause_label,llm_model,screenshot_path,replay_url,exhume_attempts,extracted_text,eulogy FROM graves')
rows = cur.fetchall()
print('slug | cause | model | attempts | screenshot | replay')
for r in rows:
    slug,name,cause,model,screen,replay,attempts_json,text,eulogy = r
    attempts = json.loads(attempts_json) if attempts_json else []
    # pick first attempt with status ok
    snap_ts = ''
    status = ''
    chars = 0
    snippet = ''
    for a in attempts:
        if a.get('status')=='ok':
            snap_ts = a.get('ts','')
            status = a.get('status','')
            chars = a.get('chars',0)
            snippet = (a.get('text') or '')[:150]
            break
    if not snap_ts and attempts:
        a = attempts[0]
        snap_ts = a.get('ts','')
        status = a.get('status','')
        chars = a.get('chars',0)
        snippet = (a.get('text') or '')[:150]
    print(f"{slug} | {cause} | {model} | {status} {snap_ts} chars={chars} | {screen} | {replay}")
    print(f"  snippet: {snippet[:150]}")
