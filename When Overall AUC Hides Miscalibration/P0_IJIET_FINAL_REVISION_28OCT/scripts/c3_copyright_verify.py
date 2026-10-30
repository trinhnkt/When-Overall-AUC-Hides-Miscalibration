import win32com.client as w

from msedit import PATHS

app = w.Dispatch("Word.Application")
app.Visible = False
try:
    for p in PATHS:
        d = app.Documents.Open(str(p), ReadOnly=True)
        links = [(h.TextToDisplay, h.Address) for h in d.Hyperlinks]
        last = d.Paragraphs(d.Paragraphs.Count - 4).Range.Text if d.Paragraphs.Count > 4 else ""
        print(p.name[-30:], len(links), links[-1:])
        d.Close(False)
finally:
    app.Quit()
