CREATE TABLE dbmail_messageblks (
    messageblk_idnr BIGINT AUTO_INCREMENT PRIMARY KEY,
    physmessage_id BIGINT,
    messageblk LONGBLOB NOT NULL,
    blocksize BIGINT DEFAULT 0 NOT NULL,
    is_header SMALLINT DEFAULT 0 NOT NULL,
    FOREIGN KEY (physmessage_id) REFERENCES dbmail_physmessage(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX dbmail_messageblks_physmessage_idx
    ON dbmail_messageblks(physmessage_id);

CREATE INDEX dbmail_messageblks_physmessage_is_header_idx
    ON dbmail_messageblks(physmessage_id, is_header);
