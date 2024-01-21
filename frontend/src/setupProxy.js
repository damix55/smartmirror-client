const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/assistant',
    createProxyMiddleware({
      target: 'http://assistant:5000',
      changeOrigin: true,
    })
  );

  app.use(
    '/video',
    createProxyMiddleware({
      target: 'http://video:7000',
      changeOrigin: true,
    })
  );
};