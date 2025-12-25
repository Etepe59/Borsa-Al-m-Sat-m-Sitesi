from flask import Flask, render_template, request, redirect, url_for
import csv

app = Flask(__name__)

# --- VERİ YAPILARI ---
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def get_all(self):
        return self.items[::-1]

class TreeNode:
    def __init__(self, ad, fiyat):
        self.ad = ad
        self.fiyat = fiyat
        self.left = None
        self.right = None

class BST:
    def __init__(self):
        self.root = None

    def insert(self, ad, fiyat):
        if not self.root:
            self.root = TreeNode(ad, fiyat)
        else:
            self._insert(self.root, ad, fiyat)

    def _insert(self, node, ad, fiyat):
        if fiyat < node.fiyat:
            if node.left:
                self._insert(node.left, ad, fiyat)
            else:
                node.left = TreeNode(ad, fiyat)
        else:
            if node.right:
                self._insert(node.right, ad, fiyat)
            else:
                node.right = TreeNode(ad, fiyat)

    def inorder(self, node, liste):
        if node:
            self.inorder(node.left, liste)
            liste.append({"ad": node.ad, "fiyat": node.fiyat})
            self.inorder(node.right, liste)

# --- GLOBAL NESNELER ---
bakiye = {"miktar": 0}  # başlangıç bakiyesi
hisseler_bst = BST()
hisseler_sozluk = {}
portfoy = {}
islem_stack = Stack()

# --- CSV'DEN TOPLU HİSSE YÜKLEME ---
def hisseleri_csvden_yukle(dosya_yolu):
    eklenen = 0

    with open(dosya_yolu, encoding="utf-8") as f:
        sample = f.read(1024)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        reader = csv.DictReader(f, dialect=dialect)

        for row in reader:
            try:
                ad = (row.get("ad") or row.get("Sembol")).upper()
                fiyat = int(float(row.get("fiyat") or row.get("Fiyat")))

                hisseler_bst.insert(ad, fiyat)
                hisseler_sozluk[ad] = fiyat
                eklenen += 1
            except:
                continue

    return eklenen

@app.route("/")
def index():
    sirali = []
    hisseler_bst.inorder(hisseler_bst.root, sirali)
    return render_template(
        "index.html",
        bakiye=bakiye["miktar"],
        hisseler=sirali,
        portfoy=portfoy,
        gecmis=islem_stack.get_all(),
        mesaj=request.args.get("mesaj")
    )

@app.route("/bakiye_ekle", methods=["POST"])
def bakiye_ekle():
    bakiye["miktar"] += int(request.form["miktar"])
    return redirect(url_for("index"))

@app.route("/hisse_ekle", methods=["GET", "POST"])
def hisse_ekle():
    if request.method == "POST":
        ad = request.form["ad"].upper()
        fiyat = int(request.form["fiyat"])
        hisseler_bst.insert(ad, fiyat)
        hisseler_sozluk[ad] = fiyat
        return redirect(url_for("index"))
    return render_template("hisse_ekle.html")

@app.route("/csv_yukle", methods=["POST"])
def csv_yukle():

    if "csv" not in request.files:
        return redirect(url_for("index", mesaj="csv_hata"))

    dosya = request.files["csv"]
    if dosya.filename == "":
        return redirect(url_for("index", mesaj="csv_hata"))

    dosya_yolu = "hisseler.csv"
    dosya.save(dosya_yolu)

    try:
        adet = hisseleri_csvden_yukle(dosya_yolu)
    except Exception as e:
        print("CSV HATASI:", e)
        return redirect(url_for("index", mesaj="csv_hata"))

    return redirect(url_for("index", mesaj=f"csv_ok_{adet}"))

@app.route("/satin_al", methods=["GET", "POST"])
def satin_al():
    if request.method == "POST":
        ad = request.form["ad"]
        adet = int(request.form["adet"])
        toplam = hisseler_sozluk[ad] * adet

        if toplam > bakiye["miktar"]:
            return redirect(url_for("index", mesaj="yetersiz"))

        bakiye["miktar"] -= toplam
        portfoy[ad] = portfoy.get(ad, 0) + adet
        islem_stack.push({"ad": ad, "adet": adet, "toplam": toplam, "tip": "AL"})
        return redirect(url_for("index", mesaj="alindi"))

    return render_template("satin_al.html", hisseler=hisseler_sozluk.keys())

@app.route("/sat", methods=["GET", "POST"])
def sat():
    if request.method == "POST":
        ad = request.form["ad"]
        adet = int(request.form["adet"])

        if ad not in portfoy or portfoy[ad] < adet:
            return redirect(url_for("index", mesaj="satamaz"))

        toplam = hisseler_sozluk[ad] * adet
        bakiye["miktar"] += toplam
        portfoy[ad] -= adet
        if portfoy[ad] == 0 :
            del portfoy[ad]

        islem_stack.push({"ad": ad, "adet": adet, "toplam": toplam, "tip": "SAT"})
        return redirect(url_for("index", mesaj="satildi"))

    return render_template("sat.html", portfoy=portfoy)

if __name__ == "__main__":
    app.run(debug=True, port=5005)