FROM postgres:15-alpine

# Ensure the source path for COPY is correct relative to your build context.
# Based on your project structure image, the custom config is at 'database/postgresql.conf'
# If your build context for docker-compose is the project root:
COPY database/postgresql.conf /etc/postgresql/postgresql.conf
# If your build context for docker-compose is the 'docker' directory itself, then it would be:
# COPY data/postgresql.conf /etc/postgresql/postgresql.conf
# Or even ../database/postgresql.conf if the context is docker/

# Start PostgreSQL using the custom configuration file from the copied location
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]