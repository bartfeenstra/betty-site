'use strict'

function initializePlatform () {
    const navigatorPlatform = navigator.platform.toLowerCase()
    let platform
    if ('win' in navigatorPlatform) {
       platform = 'windows'
    }
    else if ('mac' in navigatorPlatform) {
        platform = 'mac-os'
    }
    else if ('linux' in navigatorPlatform) {
        platform = 'linux'
    }
    else {
        platform = 'any'
    }
  const platforms = document.getElementsByClassName('platform-detection')
  for (const platform of platforms) {
      platform.classList.add('platform-detected-' + platform)
  }
}

// @todo Can we safely do this much earlier than DOMContentLoaded?
document.addEventListener('DOMContentLoaded', initializePlatform)
