module.exports = ({ config }) => {
  const host = process.env.EXPO_PUBLIC_LOGIN_HOST?.trim();
  if (host && !/^[a-z0-9]+([.-][a-z0-9]+)*\.[a-z]{2,}$/i.test(host)) throw new Error('EXPO_PUBLIC_LOGIN_HOST must be a domain name without scheme or path.');
  return {
    ...config,
    plugins: [...(config.plugins ?? []),
      ['expo-audio', { microphonePermission: false, recordAudioAndroid: false, enableBackgroundPlayback: false, enableBackgroundRecording: false }],
      ['expo-video', { supportsBackgroundPlayback: false, supportsPictureInPicture: false }],
    ],
    scheme: 'swipeiq',
    android: {
      ...config.android,
      package: 'com.swipeiq.mobile',
      ...(host ? { intentFilters: [{ action: 'VIEW', autoVerify: true,
        category: ['BROWSABLE', 'DEFAULT'], data: [{ scheme: 'https', host, pathPrefix: '/login' }] }] } : {}),
    },
  };
};
