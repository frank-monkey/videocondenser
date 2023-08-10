# Maintainer: Frank Sacco <franka25sacco at gm@il dot com>

pkgname=videocondenser-git
pkgver=0.1
pkgrel=1
pkgdesc="A tool that condenses videos by adjusting playback speed based on volume."
arch=('x86_64')
url="https://github.com/frank-monkey/videocondenser"
license=('GPL')
depends=(
    'python'
    'python-numpy'
    'python-audiotsm'
    'python-scipy'
    'ffmpeg'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-wheel'
    'git'
)
source=("${pkgname}::git+https://github.com/frank-monkey/videocondenser.git")
sha256sums=('SKIP')

pkgver() {
  cd "${pkgname}"
  git describe
}

build() {
    cd "${pkgname}"
    python -m build --wheel --no-isolation
    make
}

package() {
    cd "${pkgname}"
    python -m installer --destdir="$pkgdir" dist/*.whl
}
