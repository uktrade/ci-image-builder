# Changelog

## [1.6.0](https://github.com/uktrade/ci-image-builder/compare/1.5.0...1.6.0) (2025-03-12)


### Features

* Add Ruby support ([#83](https://github.com/uktrade/ci-image-builder/issues/83)) ([f41f21f](https://github.com/uktrade/ci-image-builder/commit/f41f21f91f8f906b1b7051261ec0a48cf9a844c9))
* Added ability to specify a branch as an env var ([#80](https://github.com/uktrade/ci-image-builder/issues/80)) ([9b3881b](https://github.com/uktrade/ci-image-builder/commit/9b3881bd2a115511ee111751a3355fc2afa61791))
* dbtp 1659 datadog ([#102](https://github.com/uktrade/ci-image-builder/issues/102)) ([8d96657](https://github.com/uktrade/ci-image-builder/commit/8d96657fffa4b465824902f48203ff6ed2f43835))
* DBTP-1026 Allow for status report of deploy phase ([#70](https://github.com/uktrade/ci-image-builder/issues/70)) ([b7e1520](https://github.com/uktrade/ci-image-builder/commit/b7e1520c79f67cf59c44ceb034878b741847fc4c))
* DBTP-1521 Failure to post to slack can cause copilot deployment to fail ([#86](https://github.com/uktrade/ci-image-builder/issues/86)) ([43088fe](https://github.com/uktrade/ci-image-builder/commit/43088fe3c5d6e1d3e98effebe1f65a3bd5d920d0))
* DBTP-1682 Add release process to ci image builder ([#87](https://github.com/uktrade/ci-image-builder/issues/87)) ([79ea7ee](https://github.com/uktrade/ci-image-builder/commit/79ea7ee0b5812e47c9a710d96681a6791027be8a))
* DBTP-765 - copilot version notifications ([#54](https://github.com/uktrade/ci-image-builder/issues/54)) ([e3e9bbd](https://github.com/uktrade/ci-image-builder/commit/e3e9bbd270489581f90042c1eede40f42a4cd08c))
* Support for pushing to two repositories ([#52](https://github.com/uktrade/ci-image-builder/issues/52)) ([ad54cd5](https://github.com/uktrade/ci-image-builder/commit/ad54cd505fe26877c113c0ebb0cc116ac5c8d540))
* support non pip installations ([#55](https://github.com/uktrade/ci-image-builder/issues/55)) ([a3d5a26](https://github.com/uktrade/ci-image-builder/commit/a3d5a269d593ae874fb0bdf1f84cc8d1b28f9ade))


### Bug Fixes

* Change release please to python ([#97](https://github.com/uktrade/ci-image-builder/issues/97)) ([1c7cd72](https://github.com/uktrade/ci-image-builder/commit/1c7cd7251968b0b67ba9d74151728f840b17bae4))
* Clear release change log ([#96](https://github.com/uktrade/ci-image-builder/issues/96)) ([b029736](https://github.com/uktrade/ci-image-builder/commit/b029736b107d0bab0f755b2a79220627826a34e3))
* Correct AWS_PROFILE in .envrc.sample ([#75](https://github.com/uktrade/ci-image-builder/issues/75)) ([8976e6d](https://github.com/uktrade/ci-image-builder/commit/8976e6d995f03f2b2d81c636e570af5f573da1ba))
* DBTP-1138 Add progress tracking for deployments ([#72](https://github.com/uktrade/ci-image-builder/issues/72)) ([5de6814](https://github.com/uktrade/ci-image-builder/commit/5de6814b9c6a92ede8da9430b5d0e1e7485aeada))
* DBTP-763 - Install correct version of copilot ([#49](https://github.com/uktrade/ci-image-builder/issues/49)) ([40d1cfb](https://github.com/uktrade/ci-image-builder/commit/40d1cfbe0af95fc6f8782b6e5f6e8c3a784f3ef8))
* fail a build with no buildpacks ([782083f](https://github.com/uktrade/ci-image-builder/commit/782083fc6f0823765f78ed9c1e403c93a357dbe0))
* Make ECR repository overrides consistent ([#50](https://github.com/uktrade/ci-image-builder/issues/50)) ([6fb8dc0](https://github.com/uktrade/ci-image-builder/commit/6fb8dc05675e9df2796ff40a50d6ac9f963abaf3))
* only add apt buildpack if packages in config ([#53](https://github.com/uktrade/ci-image-builder/issues/53)) ([dec678d](https://github.com/uktrade/ci-image-builder/commit/dec678d9404ff4bdbd8c08546871d09803f84896))
* truncate to only show last 2500 characters of error ([#62](https://github.com/uktrade/ci-image-builder/issues/62)) ([b1b88ea](https://github.com/uktrade/ci-image-builder/commit/b1b88ea1d1372bdc0064ed80dab53e415d9f24e6))

## [1.5.0](https://github.com/uktrade/ci-image-builder/compare/1.4.0...1.5.0) (2025-03-12)


### Features

* DBTP-1816 Enable specifying a run image ([#102](https://github.com/uktrade/ci-image-builder/issues/103)) ([e01eba3](https://github.com/uktrade/ci-image-builder/commit/e01eba3fed9562997dd72a64448a599b4062a0eb))

## [1.4.0](https://github.com/uktrade/ci-image-builder/compare/1.3.1...1.4.0) (2025-03-12)


### Features

* dbtp 1659 datadog ([#102](https://github.com/uktrade/ci-image-builder/issues/102)) ([8d96657](https://github.com/uktrade/ci-image-builder/commit/8d96657fffa4b465824902f48203ff6ed2f43835))

## [1.3.1](https://github.com/uktrade/ci-image-builder/compare/1.3.0...1.3.1) (2025-01-13)


### Bug Fixes

* Change release please to python ([#97](https://github.com/uktrade/ci-image-builder/issues/97)) ([1c7cd72](https://github.com/uktrade/ci-image-builder/commit/1c7cd7251968b0b67ba9d74151728f840b17bae4))

## [1.3.0](https://github.com/uktrade/ci-image-builder/compare/1.2.1...1.3.0) (2025-01-13)


### Features

* DBTP-1521 Failure to post to slack can cause copilot deployment to fail ([#86](https://github.com/uktrade/ci-image-builder/issues/86)) ([43088fe](https://github.com/uktrade/ci-image-builder/commit/43088fe3c5d6e1d3e98effebe1f65a3bd5d920d0))
* DBTP-1682 Add release process to ci image builder ([#87](https://github.com/uktrade/ci-image-builder/issues/87)) ([79ea7ee](https://github.com/uktrade/ci-image-builder/commit/79ea7ee0b5812e47c9a710d96681a6791027be8a))


### Bug Fixes

* Clear release change log ([#96](https://github.com/uktrade/ci-image-builder/issues/96)) ([b029736](https://github.com/uktrade/ci-image-builder/commit/b029736b107d0bab0f755b2a79220627826a34e3))
