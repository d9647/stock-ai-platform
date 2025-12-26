#pg_dump -U stockai -h localhost -p 5432 stockai_dev | gzip > stock_ai_production.sql.gz


gunzip -c stock_ai_production.sql.gz | \
psql 'postgresql://neondb_owner:npg_Ik6qhNYnLw1g@ep-twilight-dust-ahy8p5yn-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'