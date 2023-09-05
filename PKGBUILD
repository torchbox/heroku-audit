# Maintainer: Jake Howard <aur at theorangeone dot net>
pkgname=heroku-audit
pkgver=0.0.1
pkgrel=1
pkgdesc="Command-line tool for reporting on specific attributes of a Heroku environment."
url="https://github.com/torchbox/heroku-audit"
license=('BSD')
arch=('any')
depends=()
source=("https://github.com/torchbox/heroku-audit/archive/${pkgver}.tar.gz")
makedepends=(python-build python-wheel pyinstaller)
sha256sums=('c840041c7027b1cf902de0ae27887285fdb122baeaa349c0d18dbe9226b5eea8')

build() {
  cd "${srcdir}"/${pkgname}-${pkgver}

  python -m venv venv
  source venv/bin/activate

  pip install -e .

  pyinstaller -F --strip heroku_audit/__main__.py --name heroku-audit --clean
}

package() {
  cd "${srcdir}"/${pkgname}-${pkgver}

  install -Dm755 dist/heroku-audit "${pkgdir}"/usr/bin/heroku-audit

  install -Dm644 README.md "${pkgdir}"/usr/share/doc/${pkgname}/README.md
  install -Dm644 LICENSE "${pkgdir}"/usr/share/licenses/${pkgname}/LICENSE
}
