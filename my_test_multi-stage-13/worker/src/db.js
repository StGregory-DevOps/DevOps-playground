import pg from 'pg';

const { Pool } = pg;

// Те же PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE через env_file
export const pool = new Pool();
