# Maintainer: Jake Howard <aur at theorangeone dot net>
pkgname=heroku-audit
pkgver=0.0.3
pkgrel=1
pkgdesc="Command-line tool for reporting on specific attributes of a Heroku environment."
url="https://github.com/torchbox/heroku-audit"
license=('BSD')
arch=('x86_64')
source=("https://github.com/torchbox/heroku-audit/releases/download/${pkgver}/heroku-audit-ubuntu-latest")
sha256sums=('26444e7b19a448e5bf548f9845000516095d4a8b5725a4f0fbd03162c541af9c')

build() {
  chmod +x "${srcdir}"/heroku-audit-ubuntu-latest
}

check() {
  "${srcdir}"/heroku-audit-ubuntu-latest --version > /dev/null
  "${srcdir}"/heroku-audit-ubuntu-latest --list > /dev/null
}

package() {
  install -D "${srcdir}"/heroku-audit-ubuntu-latest "$pkgdir"/usr/bin/heroku-audit
}
