# Maintainer: Jake Howard <aur at theorangeone dot net>
pkgname=heroku-audit
pkgver=0.0.2
pkgrel=1
pkgdesc="Command-line tool for reporting on specific attributes of a Heroku environment."
url="https://github.com/torchbox/heroku-audit"
license=('BSD')
arch=('any')
depends=(python)
source=("https://github.com/torchbox/heroku-audit/archive/${pkgver}.tar.gz")
makedepends=(python-build python-wheel)
sha256sums=('0c539746c4b5dfb1ff8504e1a96394c3456666c866e0f0c1f7f54ef6f1242279')

build() {
  cd "${srcdir}"/${pkgname}-${pkgver}

  # Create a temporary virtualenv to install the build dependencies in
  python -m venv venv
  source venv/bin/activate

  pip install -e . pyinstaller

  venv/bin/pyinstaller -F --strip heroku_audit/__main__.py --name heroku-audit --clean
}

check() {
  cd "${srcdir}"/${pkgname}-${pkgver}

  ./dist/heroku-audit --version > /dev/null
  ./dist/heroku-audit --list > /dev/null
}

package() {
  cd "${srcdir}"/${pkgname}-${pkgver}

  install -Dm755 dist/heroku-audit "${pkgdir}"/usr/bin/heroku-audit

  install -Dm644 README.md "${pkgdir}"/usr/share/doc/${pkgname}/README.md
  install -Dm644 LICENSE "${pkgdir}"/usr/share/licenses/${pkgname}/LICENSE
}
