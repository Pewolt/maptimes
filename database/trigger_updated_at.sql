CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_rss_feeds_updated_at
BEFORE UPDATE ON rss_feeds
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();
