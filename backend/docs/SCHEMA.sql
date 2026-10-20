BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial

CREATE TABLE products (
    id VARCHAR(40) NOT NULL, 
    name VARCHAR(150) NOT NULL, 
    category VARCHAR(30) NOT NULL, 
    price_inr INTEGER NOT NULL, 
    cpu_label VARCHAR(100) NOT NULL, 
    cpu_tier INTEGER NOT NULL, 
    ram_gb INTEGER NOT NULL, 
    storage_gb INTEGER NOT NULL, 
    storage_type VARCHAR(30) NOT NULL, 
    gpu_label VARCHAR(100) NOT NULL, 
    gpu_tier INTEGER NOT NULL, 
    dedicated_gpu BOOLEAN, 
    vram_gb INTEGER, 
    weight_kg FLOAT, 
    battery_hours FLOAT, 
    use_case_tags JSONB NOT NULL, 
    feature_tags JSONB NOT NULL, 
    is_synthetic BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT positive_product_values CHECK (price_inr > 0 AND ram_gb > 0 AND storage_gb > 0), 
    CONSTRAINT valid_tiers CHECK (cpu_tier BETWEEN 1 AND 5 AND gpu_tier BETWEEN 0 AND 5), 
    CONSTRAINT positive_weight CHECK (weight_kg IS NULL OR weight_kg > 0), 
    CONSTRAINT positive_battery CHECK (battery_hours IS NULL OR battery_hours > 0), 
    CONSTRAINT nonnegative_vram CHECK (vram_gb IS NULL OR vram_gb >= 0)
);

CREATE INDEX ix_products_category_price ON products (category, price_inr);

CREATE TABLE conversations (
    id VARCHAR(36) NOT NULL, 
    requirements JSONB NOT NULL, 
    state_version INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE messages (
    id VARCHAR(36) NOT NULL, 
    conversation_id VARCHAR(36) NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    content VARCHAR(16000) NOT NULL, 
    sequence INTEGER NOT NULL, 
    client_message_id VARCHAR(36), 
    response JSONB, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_message_sequence UNIQUE (conversation_id, sequence), 
    CONSTRAINT uq_client_message UNIQUE (conversation_id, client_message_id), 
    FOREIGN KEY(conversation_id) REFERENCES conversations (id)
);

CREATE INDEX ix_messages_conversation_id ON messages (conversation_id);

CREATE TABLE recommendation_runs (
    id VARCHAR(36) NOT NULL, 
    conversation_id VARCHAR(36) NOT NULL, 
    source_message_id VARCHAR(36) NOT NULL, 
    requirement_snapshot JSONB NOT NULL, 
    products JSONB NOT NULL, 
    evidence JSONB NOT NULL, 
    eligible_count INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
    FOREIGN KEY(source_message_id) REFERENCES messages (id)
);

CREATE INDEX ix_recommendation_runs_conversation_id ON recommendation_runs (conversation_id);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial') RETURNING alembic_version.version_num;

COMMIT;

