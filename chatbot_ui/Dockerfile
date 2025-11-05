FROM nginx:alpine

# Install bash and gettext for envsubst
RUN apk add --no-cache bash gettext

# Copy static files
COPY index.html /usr/share/nginx/html/
COPY example-prompts.json /usr/share/nginx/html/

# Copy nginx template (will be processed by nginx on startup)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Nginx will automatically process templates from /etc/nginx/templates/
# and substitute environment variables
CMD ["nginx", "-g", "daemon off;"]
