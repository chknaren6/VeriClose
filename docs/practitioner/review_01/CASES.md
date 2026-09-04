# Blinded practitioner cases

> Synthetic data only. System decisions and benchmark labels are intentionally hidden.

## PR-001

### GATEWAY

- `PR-001-E01` — gateway_event_id=gwe_0042_000031, event_type=PAYMENT, transaction_id=pay_0042_000031, settlement_id=set_0042_0007, amount_minor=166400, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0042_000031, narration=Synthetic captured payment

- `PR-001-E02` — gateway_event_id=gwe_0042_000032, event_type=PAYMENT, transaction_id=pay_0042_000032, settlement_id=set_0042_0007, amount_minor=121800, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0042_000032, narration=Synthetic captured payment

- `PR-001-E03` — gateway_event_id=gwe_0042_000033, event_type=PAYMENT, transaction_id=pay_0042_000033, settlement_id=set_0042_0007, amount_minor=35400, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0042_000033, narration=Synthetic captured payment

- `PR-001-E04` — gateway_event_id=gwe_0042_000034, event_type=PAYMENT, transaction_id=pay_0042_000034, settlement_id=set_0042_0007, amount_minor=110800, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0042_000034, narration=Synthetic captured payment

- `PR-001-E05` — gateway_event_id=gwe_0042_000035, event_type=PAYMENT, transaction_id=pay_0042_000035, settlement_id=set_0042_0007, amount_minor=76800, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0042_000035, narration=Synthetic captured payment

- `PR-001-E06` — gateway_event_id=gwe_fee_0042_0007, event_type=FEE, transaction_id=, settlement_id=set_0042_0007, amount_minor=12728, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=processed, reference=set_0042_0007, narration=Synthetic gateway fee

- `PR-001-E07` — gateway_event_id=gwe_tax_0042_0007, event_type=TAX, transaction_id=, settlement_id=set_0042_0007, amount_minor=2291, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=processed, reference=set_0042_0007, narration=Synthetic GST on gateway fee

- `PR-001-E08` — gateway_event_id=gwe_set_0042_0007, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0042_0007, amount_minor=496181, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=settled, reference=UTR004200000007, narration=Synthetic net settlement

### BANK

- `PR-001-E09` — bank_record_id=bnk_0042_0007, value_date=2026-04-08, booking_date=2026-04-08, credit_amount=4961.81, debit_amount=0.00, utr=UTR004200000007, narration=Synthetic settlement set_0042_0007, currency=INR, account_reference=acct_demo_01

- `PR-001-E10` — bank_record_id=bnk_0042_0007_candidate, value_date=2026-04-08, booking_date=2026-04-08, credit_amount=4961.81, debit_amount=0.00, utr=ALTUTR004200000007, narration=Synthetic equal-amount competing bank candidate, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-001-E11` — journal_id=jrn_0042_0007, line_number=1, posting_date=2026-04-08, account_code=110000, debit_amount=4961.81, credit_amount=0.00, currency=INR, external_reference=set_0042_0007, narration=Synthetic bank receipt

- `PR-001-E12` — journal_id=jrn_0042_0007, line_number=2, posting_date=2026-04-08, account_code=510000, debit_amount=127.28, credit_amount=0.00, currency=INR, external_reference=set_0042_0007, narration=Synthetic gateway fee expense

- `PR-001-E13` — journal_id=jrn_0042_0007, line_number=3, posting_date=2026-04-08, account_code=140000, debit_amount=22.91, credit_amount=0.00, currency=INR, external_reference=set_0042_0007, narration=Synthetic input GST

- `PR-001-E14` — journal_id=jrn_0042_0007, line_number=4, posting_date=2026-04-08, account_code=120000, debit_amount=0.00, credit_amount=5112.00, currency=INR, external_reference=set_0042_0007, narration=Synthetic clearing credit

## PR-002

### GATEWAY

- `PR-002-E01` — gateway_event_id=gwe_0042_000061, event_type=PAYMENT, transaction_id=pay_0042_000061, settlement_id=set_0042_0013, amount_minor=60800, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=captured, reference=order_0042_000061, narration=Synthetic captured payment

- `PR-002-E02` — gateway_event_id=gwe_0042_000062, event_type=PAYMENT, transaction_id=pay_0042_000062, settlement_id=set_0042_0013, amount_minor=160000, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=captured, reference=order_0042_000062, narration=Synthetic captured payment

- `PR-002-E03` — gateway_event_id=gwe_0042_000063, event_type=PAYMENT, transaction_id=pay_0042_000063, settlement_id=set_0042_0013, amount_minor=14900, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=captured, reference=order_0042_000063, narration=Synthetic captured payment

- `PR-002-E04` — gateway_event_id=gwe_0042_000064, event_type=PAYMENT, transaction_id=pay_0042_000064, settlement_id=set_0042_0013, amount_minor=196900, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=captured, reference=order_0042_000064, narration=Synthetic captured payment

- `PR-002-E05` — gateway_event_id=gwe_0042_000065, event_type=PAYMENT, transaction_id=pay_0042_000065, settlement_id=set_0042_0013, amount_minor=62500, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=captured, reference=order_0042_000065, narration=Synthetic captured payment

- `PR-002-E06` — gateway_event_id=gwe_fee_0042_0013, event_type=FEE, transaction_id=, settlement_id=set_0042_0013, amount_minor=9505, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=processed, reference=set_0042_0013, narration=Synthetic gateway fee

- `PR-002-E07` — gateway_event_id=gwe_tax_0042_0013, event_type=TAX, transaction_id=, settlement_id=set_0042_0013, amount_minor=1710, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=processed, reference=set_0042_0013, narration=Synthetic GST on gateway fee

- `PR-002-E08` — gateway_event_id=gwe_set_0042_0013, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0042_0013, amount_minor=483885, currency=INR, event_at=2026-04-13T10:00:00+00:00, status=settled, reference=UTR004200000013, narration=Synthetic net settlement

### BANK

- `PR-002-E09` — bank_record_id=bnk_0042_0013, value_date=2026-04-14, booking_date=2026-04-14, credit_amount=4838.85, debit_amount=0.00, utr=UTR004200000013, narration=Synthetic settlement set_0042_0013, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-002-E10` — journal_id=jrn_0042_0013, line_number=1, posting_date=2026-04-14, account_code=110000, debit_amount=4839.84, credit_amount=0.00, currency=INR, external_reference=set_0042_0013, narration=Synthetic bank receipt

- `PR-002-E11` — journal_id=jrn_0042_0013, line_number=2, posting_date=2026-04-14, account_code=510000, debit_amount=95.05, credit_amount=0.00, currency=INR, external_reference=set_0042_0013, narration=Synthetic gateway fee expense

- `PR-002-E12` — journal_id=jrn_0042_0013, line_number=3, posting_date=2026-04-14, account_code=140000, debit_amount=17.10, credit_amount=0.00, currency=INR, external_reference=set_0042_0013, narration=Synthetic input GST

- `PR-002-E13` — journal_id=jrn_0042_0013, line_number=4, posting_date=2026-04-14, account_code=120000, debit_amount=0.00, credit_amount=4951.00, currency=INR, external_reference=set_0042_0013, narration=Synthetic clearing credit

## PR-003

### GATEWAY

- `PR-003-E01` — gateway_event_id=gwe_0042_000021, event_type=PAYMENT, transaction_id=pay_0042_000021, settlement_id=set_0042_0005, amount_minor=180800, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0042_000021, narration=Synthetic captured payment

- `PR-003-E02` — gateway_event_id=gwe_0042_000022, event_type=PAYMENT, transaction_id=pay_0042_000022, settlement_id=set_0042_0005, amount_minor=152600, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0042_000022, narration=Synthetic captured payment

- `PR-003-E03` — gateway_event_id=gwe_0042_000023, event_type=PAYMENT, transaction_id=pay_0042_000023, settlement_id=set_0042_0005, amount_minor=177100, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0042_000023, narration=Synthetic captured payment

- `PR-003-E04` — gateway_event_id=gwe_0042_000024, event_type=PAYMENT, transaction_id=pay_0042_000024, settlement_id=set_0042_0005, amount_minor=142600, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0042_000024, narration=Synthetic captured payment

- `PR-003-E05` — gateway_event_id=gwe_0042_000025, event_type=PAYMENT, transaction_id=pay_0042_000025, settlement_id=set_0042_0005, amount_minor=191700, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0042_000025, narration=Synthetic captured payment

- `PR-003-E06` — gateway_event_id=gwe_fee_0042_0005, event_type=FEE, transaction_id=, settlement_id=set_0042_0005, amount_minor=15713, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=processed, reference=set_0042_0005, narration=Synthetic gateway fee

- `PR-003-E07` — gateway_event_id=gwe_tax_0042_0005, event_type=TAX, transaction_id=, settlement_id=set_0042_0005, amount_minor=2828, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=processed, reference=set_0042_0005, narration=Synthetic GST on gateway fee

- `PR-003-E08` — gateway_event_id=gwe_set_0042_0005, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0042_0005, amount_minor=826259, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=settled, reference=UTR004200000005, narration=Synthetic net settlement

### BANK

- `PR-003-E09` — bank_record_id=bnk_0042_0005, value_date=2026-04-06, booking_date=2026-04-06, credit_amount=8262.59, debit_amount=0.00, utr=UTR00420000000X, narration=Synthetic settlement set_0042_0005, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-003-E10` — journal_id=jrn_0042_0005, line_number=1, posting_date=2026-04-06, account_code=110000, debit_amount=8262.59, credit_amount=0.00, currency=INR, external_reference=set_0042_0005, narration=Synthetic bank receipt

- `PR-003-E11` — journal_id=jrn_0042_0005, line_number=2, posting_date=2026-04-06, account_code=510000, debit_amount=157.13, credit_amount=0.00, currency=INR, external_reference=set_0042_0005, narration=Synthetic gateway fee expense

- `PR-003-E12` — journal_id=jrn_0042_0005, line_number=3, posting_date=2026-04-06, account_code=140000, debit_amount=28.28, credit_amount=0.00, currency=INR, external_reference=set_0042_0005, narration=Synthetic input GST

- `PR-003-E13` — journal_id=jrn_0042_0005, line_number=4, posting_date=2026-04-06, account_code=120000, debit_amount=0.00, credit_amount=8448.00, currency=INR, external_reference=set_0042_0005, narration=Synthetic clearing credit

## PR-004

### GATEWAY

- `PR-004-E01` — gateway_event_id=gwe_0042_000041, event_type=PAYMENT, transaction_id=pay_0042_000041, settlement_id=set_0042_0009, amount_minor=38500, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0042_000041, narration=Synthetic captured payment

- `PR-004-E02` — gateway_event_id=gwe_0042_000042, event_type=PAYMENT, transaction_id=pay_0042_000042, settlement_id=set_0042_0009, amount_minor=77000, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0042_000042, narration=Synthetic captured payment

- `PR-004-E03` — gateway_event_id=gwe_0042_000043, event_type=PAYMENT, transaction_id=pay_0042_000043, settlement_id=set_0042_0009, amount_minor=166500, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0042_000043, narration=Synthetic captured payment

- `PR-004-E04` — gateway_event_id=gwe_0042_000044, event_type=PAYMENT, transaction_id=pay_0042_000044, settlement_id=set_0042_0009, amount_minor=66500, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0042_000044, narration=Synthetic captured payment

- `PR-004-E05` — gateway_event_id=gwe_0042_000045, event_type=PAYMENT, transaction_id=pay_0042_000045, settlement_id=set_0042_0009, amount_minor=39800, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0042_000045, narration=Synthetic captured payment

- `PR-004-E06` — gateway_event_id=gwe_fee_0042_0009, event_type=FEE, transaction_id=, settlement_id=set_0042_0009, amount_minor=7116, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=processed, reference=set_0042_0009, narration=Synthetic gateway fee

- `PR-004-E07` — gateway_event_id=gwe_tax_0042_0009, event_type=TAX, transaction_id=, settlement_id=set_0042_0009, amount_minor=1258, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=processed, reference=set_0042_0009, narration=Synthetic GST on gateway fee

- `PR-004-E08` — gateway_event_id=gwe_set_0042_0009, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0042_0009, amount_minor=380053, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=settled, reference=UTR004200000009, narration=Synthetic net settlement

### BANK

- `PR-004-E09` — bank_record_id=bnk_0042_0009, value_date=2026-04-10, booking_date=2026-04-10, credit_amount=3800.53, debit_amount=0.00, utr=UTR004200000009, narration=Synthetic settlement set_0042_0009, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-004-E10` — journal_id=jrn_0042_0009, line_number=1, posting_date=2026-04-10, account_code=110000, debit_amount=3800.53, credit_amount=0.00, currency=INR, external_reference=set_0042_0009, narration=Synthetic bank receipt

- `PR-004-E11` — journal_id=jrn_0042_0009, line_number=2, posting_date=2026-04-10, account_code=510000, debit_amount=69.89, credit_amount=0.00, currency=INR, external_reference=set_0042_0009, narration=Synthetic gateway fee expense

- `PR-004-E12` — journal_id=jrn_0042_0009, line_number=3, posting_date=2026-04-10, account_code=140000, debit_amount=12.58, credit_amount=0.00, currency=INR, external_reference=set_0042_0009, narration=Synthetic input GST

- `PR-004-E13` — journal_id=jrn_0042_0009, line_number=4, posting_date=2026-04-10, account_code=120000, debit_amount=0.00, credit_amount=3883.00, currency=INR, external_reference=set_0042_0009, narration=Synthetic clearing credit

## PR-005

### GATEWAY

- `PR-005-E01` — gateway_event_id=gwe_0042_000001, event_type=PAYMENT, transaction_id=pay_0042_000001, settlement_id=set_0042_0001, amount_minor=190100, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0042_000001, narration=Synthetic captured payment

- `PR-005-E02` — gateway_event_id=gwe_0042_000002, event_type=PAYMENT, transaction_id=pay_0042_000002, settlement_id=set_0042_0001, amount_minor=50100, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0042_000002, narration=Synthetic captured payment

- `PR-005-E03` — gateway_event_id=gwe_0042_000003, event_type=PAYMENT, transaction_id=pay_0042_000003, settlement_id=set_0042_0001, amount_minor=38600, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0042_000003, narration=Synthetic captured payment

- `PR-005-E04` — gateway_event_id=gwe_0042_000004, event_type=PAYMENT, transaction_id=pay_0042_000004, settlement_id=set_0042_0001, amount_minor=55300, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0042_000004, narration=Synthetic captured payment

- `PR-005-E05` — gateway_event_id=gwe_0042_000005, event_type=PAYMENT, transaction_id=pay_0042_000005, settlement_id=set_0042_0001, amount_minor=59900, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0042_000005, narration=Synthetic captured payment

- `PR-005-E06` — gateway_event_id=gwe_fee_0042_0001, event_type=FEE, transaction_id=, settlement_id=set_0042_0001, amount_minor=7958, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0042_0001, narration=Synthetic gateway fee

- `PR-005-E07` — gateway_event_id=gwe_tax_0042_0001, event_type=TAX, transaction_id=, settlement_id=set_0042_0001, amount_minor=1432, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0042_0001, narration=Synthetic GST on gateway fee

- `PR-005-E08` — gateway_event_id=gwe_set_0042_0001, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0042_0001, amount_minor=384610, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=settled, reference=UTR004200000001, narration=Synthetic net settlement

### BANK

- `PR-005-E09` — bank_record_id=bnk_0042_0001, value_date=2026-04-02, booking_date=2026-04-02, credit_amount=3846.10, debit_amount=0.00, utr=UTR004200000001, narration=Synthetic settlement set_0042_0001, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-005-E10` — journal_id=jrn_0042_0001, line_number=1, posting_date=2026-04-02, account_code=110000, debit_amount=3846.10, credit_amount=0.00, currency=INR, external_reference=set_0042_0001, narration=Synthetic bank receipt

- `PR-005-E11` — journal_id=jrn_0042_0001, line_number=2, posting_date=2026-04-02, account_code=510000, debit_amount=79.58, credit_amount=0.00, currency=INR, external_reference=set_0042_0001, narration=Synthetic gateway fee expense

- `PR-005-E12` — journal_id=jrn_0042_0001, line_number=3, posting_date=2026-04-02, account_code=140000, debit_amount=14.32, credit_amount=0.00, currency=INR, external_reference=set_0042_0001, narration=Synthetic input GST

- `PR-005-E13` — journal_id=jrn_0042_0001, line_number=4, posting_date=2026-04-02, account_code=120000, debit_amount=0.00, credit_amount=3940.00, currency=INR, external_reference=set_0042_0001, narration=Synthetic clearing credit

## PR-006

### GATEWAY

- `PR-006-E01` — gateway_event_id=gwe_0073_000116, event_type=PAYMENT, transaction_id=pay_0073_000116, settlement_id=set_0073_0024, amount_minor=181500, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=captured, reference=order_0073_000116, narration=Synthetic captured payment

- `PR-006-E02` — gateway_event_id=gwe_0073_000117, event_type=PAYMENT, transaction_id=pay_0073_000117, settlement_id=set_0073_0024, amount_minor=61400, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=captured, reference=order_0073_000117, narration=Synthetic captured payment

- `PR-006-E03` — gateway_event_id=gwe_0073_000118, event_type=PAYMENT, transaction_id=pay_0073_000118, settlement_id=set_0073_0024, amount_minor=116700, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=captured, reference=order_0073_000118, narration=Synthetic captured payment

- `PR-006-E04` — gateway_event_id=gwe_0073_000119, event_type=PAYMENT, transaction_id=pay_0073_000119, settlement_id=set_0073_0024, amount_minor=38300, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=captured, reference=order_0073_000119, narration=Synthetic captured payment

- `PR-006-E05` — gateway_event_id=gwe_0073_000120, event_type=PAYMENT, transaction_id=pay_0073_000120, settlement_id=set_0073_0024, amount_minor=179500, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=captured, reference=order_0073_000120, narration=Synthetic captured payment

- `PR-006-E06` — gateway_event_id=gwe_fee_0073_0024, event_type=FEE, transaction_id=, settlement_id=set_0073_0024, amount_minor=15012, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=processed, reference=set_0073_0024, narration=Synthetic gateway fee

- `PR-006-E07` — gateway_event_id=gwe_tax_0073_0024, event_type=TAX, transaction_id=, settlement_id=set_0073_0024, amount_minor=2702, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=processed, reference=set_0073_0024, narration=Synthetic GST on gateway fee

- `PR-006-E08` — gateway_event_id=gwe_set_0073_0024, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0073_0024, amount_minor=559686, currency=INR, event_at=2026-04-24T10:00:00+00:00, status=settled, reference=UTR007300000024, narration=Synthetic net settlement

### BANK

- `PR-006-E09` — bank_record_id=bnk_0073_0024, value_date=2026-04-25, booking_date=2026-04-25, credit_amount=5596.86, debit_amount=0.00, utr=UTR007300000024, narration=Synthetic settlement set_0073_0024, currency=INR, account_reference=acct_demo_01

- `PR-006-E10` — bank_record_id=bnk_0073_0024_candidate, value_date=2026-04-25, booking_date=2026-04-25, credit_amount=5596.86, debit_amount=0.00, utr=ALTUTR007300000024, narration=Synthetic equal-amount competing bank candidate, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-006-E11` — journal_id=jrn_0073_0024, line_number=1, posting_date=2026-04-25, account_code=110000, debit_amount=5596.86, credit_amount=0.00, currency=INR, external_reference=set_0073_0024, narration=Synthetic bank receipt

- `PR-006-E12` — journal_id=jrn_0073_0024, line_number=2, posting_date=2026-04-25, account_code=510000, debit_amount=150.12, credit_amount=0.00, currency=INR, external_reference=set_0073_0024, narration=Synthetic gateway fee expense

- `PR-006-E13` — journal_id=jrn_0073_0024, line_number=3, posting_date=2026-04-25, account_code=140000, debit_amount=27.02, credit_amount=0.00, currency=INR, external_reference=set_0073_0024, narration=Synthetic input GST

- `PR-006-E14` — journal_id=jrn_0073_0024, line_number=4, posting_date=2026-04-25, account_code=120000, debit_amount=0.00, credit_amount=5774.00, currency=INR, external_reference=set_0073_0024, narration=Synthetic clearing credit

## PR-007

### GATEWAY

- `PR-007-E01` — gateway_event_id=gwe_0073_000086, event_type=PAYMENT, transaction_id=pay_0073_000086, settlement_id=set_0073_0018, amount_minor=53300, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0073_000086, narration=Synthetic captured payment

- `PR-007-E02` — gateway_event_id=gwe_0073_000087, event_type=PAYMENT, transaction_id=pay_0073_000087, settlement_id=set_0073_0018, amount_minor=113600, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0073_000087, narration=Synthetic captured payment

- `PR-007-E03` — gateway_event_id=gwe_0073_000088, event_type=PAYMENT, transaction_id=pay_0073_000088, settlement_id=set_0073_0018, amount_minor=113900, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0073_000088, narration=Synthetic captured payment

- `PR-007-E04` — gateway_event_id=gwe_0073_000089, event_type=PAYMENT, transaction_id=pay_0073_000089, settlement_id=set_0073_0018, amount_minor=139000, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0073_000089, narration=Synthetic captured payment

- `PR-007-E05` — gateway_event_id=gwe_0073_000090, event_type=PAYMENT, transaction_id=pay_0073_000090, settlement_id=set_0073_0018, amount_minor=22600, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0073_000090, narration=Synthetic captured payment

- `PR-007-E06` — gateway_event_id=gwe_fee_0073_0018, event_type=FEE, transaction_id=, settlement_id=set_0073_0018, amount_minor=9290, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=processed, reference=set_0073_0018, narration=Synthetic gateway fee

- `PR-007-E07` — gateway_event_id=gwe_tax_0073_0018, event_type=TAX, transaction_id=, settlement_id=set_0073_0018, amount_minor=1672, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=processed, reference=set_0073_0018, narration=Synthetic GST on gateway fee

- `PR-007-E08` — gateway_event_id=gwe_set_0073_0018, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0073_0018, amount_minor=431438, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=settled, reference=UTR007300000018, narration=Synthetic net settlement

### BANK

- `PR-007-E09` — bank_record_id=bnk_0073_0018, value_date=2026-04-19, booking_date=2026-04-19, credit_amount=4314.38, debit_amount=0.00, utr=UTR007300000018, narration=Synthetic settlement set_0073_0018, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-007-E10` — journal_id=jrn_0073_0018, line_number=1, posting_date=2026-04-19, account_code=110000, debit_amount=4315.37, credit_amount=0.00, currency=INR, external_reference=set_0073_0018, narration=Synthetic bank receipt

- `PR-007-E11` — journal_id=jrn_0073_0018, line_number=2, posting_date=2026-04-19, account_code=510000, debit_amount=92.90, credit_amount=0.00, currency=INR, external_reference=set_0073_0018, narration=Synthetic gateway fee expense

- `PR-007-E12` — journal_id=jrn_0073_0018, line_number=3, posting_date=2026-04-19, account_code=140000, debit_amount=16.72, credit_amount=0.00, currency=INR, external_reference=set_0073_0018, narration=Synthetic input GST

- `PR-007-E13` — journal_id=jrn_0073_0018, line_number=4, posting_date=2026-04-19, account_code=120000, debit_amount=0.00, credit_amount=4424.00, currency=INR, external_reference=set_0073_0018, narration=Synthetic clearing credit

## PR-008

### GATEWAY

- `PR-008-E01` — gateway_event_id=gwe_0073_000041, event_type=PAYMENT, transaction_id=pay_0073_000041, settlement_id=set_0073_0009, amount_minor=163900, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0073_000041, narration=Synthetic captured payment

- `PR-008-E02` — gateway_event_id=gwe_0073_000042, event_type=PAYMENT, transaction_id=pay_0073_000042, settlement_id=set_0073_0009, amount_minor=117700, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0073_000042, narration=Synthetic captured payment

- `PR-008-E03` — gateway_event_id=gwe_0073_000043, event_type=PAYMENT, transaction_id=pay_0073_000043, settlement_id=set_0073_0009, amount_minor=97600, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0073_000043, narration=Synthetic captured payment

- `PR-008-E04` — gateway_event_id=gwe_0073_000044, event_type=PAYMENT, transaction_id=pay_0073_000044, settlement_id=set_0073_0009, amount_minor=187300, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0073_000044, narration=Synthetic captured payment

- `PR-008-E05` — gateway_event_id=gwe_0073_000045, event_type=PAYMENT, transaction_id=pay_0073_000045, settlement_id=set_0073_0009, amount_minor=134500, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0073_000045, narration=Synthetic captured payment

- `PR-008-E06` — gateway_event_id=gwe_fee_0073_0009, event_type=FEE, transaction_id=, settlement_id=set_0073_0009, amount_minor=17595, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=processed, reference=set_0073_0009, narration=Synthetic gateway fee

- `PR-008-E07` — gateway_event_id=gwe_tax_0073_0009, event_type=TAX, transaction_id=, settlement_id=set_0073_0009, amount_minor=3167, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=processed, reference=set_0073_0009, narration=Synthetic GST on gateway fee

- `PR-008-E08` — gateway_event_id=gwe_set_0073_0009, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0073_0009, amount_minor=680238, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=settled, reference=UTR007300000009, narration=Synthetic net settlement

### BANK

- `PR-008-E09` — bank_record_id=bnk_0073_0009, value_date=2026-04-10, booking_date=2026-04-10, credit_amount=6802.38, debit_amount=0.00, utr=UTR007300000009, narration=Synthetic settlement set_0073_0009, currency=INR, account_reference=acct_demo_01

### ERP

No source row is present.

## PR-009

### GATEWAY

- `PR-009-E01` — gateway_event_id=gwe_0073_000021, event_type=PAYMENT, transaction_id=pay_0073_000021, settlement_id=set_0073_0005, amount_minor=98500, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0073_000021, narration=Synthetic captured payment

- `PR-009-E02` — gateway_event_id=gwe_0073_000022, event_type=PAYMENT, transaction_id=pay_0073_000022, settlement_id=set_0073_0005, amount_minor=9600, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0073_000022, narration=Synthetic captured payment

- `PR-009-E03` — gateway_event_id=gwe_0073_000023, event_type=PAYMENT, transaction_id=pay_0073_000023, settlement_id=set_0073_0005, amount_minor=75300, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0073_000023, narration=Synthetic captured payment

- `PR-009-E04` — gateway_event_id=gwe_0073_000024, event_type=PAYMENT, transaction_id=pay_0073_000024, settlement_id=set_0073_0005, amount_minor=28900, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0073_000024, narration=Synthetic captured payment

- `PR-009-E05` — gateway_event_id=gwe_0073_000025, event_type=PAYMENT, transaction_id=pay_0073_000025, settlement_id=set_0073_0005, amount_minor=72400, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0073_000025, narration=Synthetic captured payment

- `PR-009-E06` — gateway_event_id=gwe_fee_0073_0005, event_type=FEE, transaction_id=, settlement_id=set_0073_0005, amount_minor=5352, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=processed, reference=set_0073_0005, narration=Synthetic gateway fee

- `PR-009-E07` — gateway_event_id=gwe_tax_0073_0005, event_type=TAX, transaction_id=, settlement_id=set_0073_0005, amount_minor=963, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=processed, reference=set_0073_0005, narration=Synthetic GST on gateway fee

- `PR-009-E08` — gateway_event_id=gwe_set_0073_0005, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0073_0005, amount_minor=278385, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=settled, reference=UTR007300000005, narration=Synthetic net settlement

### BANK

- `PR-009-E09` — bank_record_id=bnk_0073_0005, value_date=2026-04-06, booking_date=2026-04-06, credit_amount=2784.86, debit_amount=0.00, utr=UTR007300000005, narration=Synthetic settlement set_0073_0005, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-009-E10` — journal_id=jrn_0073_0005, line_number=1, posting_date=2026-04-06, account_code=110000, debit_amount=2783.85, credit_amount=0.00, currency=INR, external_reference=set_0073_0005, narration=Synthetic bank receipt

- `PR-009-E11` — journal_id=jrn_0073_0005, line_number=2, posting_date=2026-04-06, account_code=510000, debit_amount=53.52, credit_amount=0.00, currency=INR, external_reference=set_0073_0005, narration=Synthetic gateway fee expense

- `PR-009-E12` — journal_id=jrn_0073_0005, line_number=3, posting_date=2026-04-06, account_code=140000, debit_amount=9.63, credit_amount=0.00, currency=INR, external_reference=set_0073_0005, narration=Synthetic input GST

- `PR-009-E13` — journal_id=jrn_0073_0005, line_number=4, posting_date=2026-04-06, account_code=120000, debit_amount=0.00, credit_amount=2847.00, currency=INR, external_reference=set_0073_0005, narration=Synthetic clearing credit

## PR-010

### GATEWAY

- `PR-010-E01` — gateway_event_id=gwe_0073_000001, event_type=PAYMENT, transaction_id=pay_0073_000001, settlement_id=set_0073_0001, amount_minor=153500, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0073_000001, narration=Synthetic captured payment

- `PR-010-E02` — gateway_event_id=gwe_0073_000002, event_type=PAYMENT, transaction_id=pay_0073_000002, settlement_id=set_0073_0001, amount_minor=77200, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0073_000002, narration=Synthetic captured payment

- `PR-010-E03` — gateway_event_id=gwe_0073_000003, event_type=PAYMENT, transaction_id=pay_0073_000003, settlement_id=set_0073_0001, amount_minor=71700, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0073_000003, narration=Synthetic captured payment

- `PR-010-E04` — gateway_event_id=gwe_0073_000004, event_type=PAYMENT, transaction_id=pay_0073_000004, settlement_id=set_0073_0001, amount_minor=29600, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0073_000004, narration=Synthetic captured payment

- `PR-010-E05` — gateway_event_id=gwe_0073_000005, event_type=PAYMENT, transaction_id=pay_0073_000005, settlement_id=set_0073_0001, amount_minor=8900, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0073_000005, narration=Synthetic captured payment

- `PR-010-E06` — gateway_event_id=gwe_fee_0073_0001, event_type=FEE, transaction_id=, settlement_id=set_0073_0001, amount_minor=8113, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0073_0001, narration=Synthetic gateway fee

- `PR-010-E07` — gateway_event_id=gwe_tax_0073_0001, event_type=TAX, transaction_id=, settlement_id=set_0073_0001, amount_minor=1460, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0073_0001, narration=Synthetic GST on gateway fee

- `PR-010-E08` — gateway_event_id=gwe_set_0073_0001, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0073_0001, amount_minor=331327, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=settled, reference=UTR007300000001, narration=Synthetic net settlement

### BANK

- `PR-010-E09` — bank_record_id=bnk_0073_0001, value_date=2026-04-02, booking_date=2026-04-02, credit_amount=3313.27, debit_amount=0.00, utr=UTR007300000001, narration=Synthetic settlement set_0073_0001, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-010-E10` — journal_id=jrn_0073_0001, line_number=1, posting_date=2026-04-02, account_code=110000, debit_amount=3313.27, credit_amount=0.00, currency=INR, external_reference=set_0073_0001, narration=Synthetic bank receipt

- `PR-010-E11` — journal_id=jrn_0073_0001, line_number=2, posting_date=2026-04-02, account_code=510000, debit_amount=81.13, credit_amount=0.00, currency=INR, external_reference=set_0073_0001, narration=Synthetic gateway fee expense

- `PR-010-E12` — journal_id=jrn_0073_0001, line_number=3, posting_date=2026-04-02, account_code=140000, debit_amount=14.60, credit_amount=0.00, currency=INR, external_reference=set_0073_0001, narration=Synthetic input GST

- `PR-010-E13` — journal_id=jrn_0073_0001, line_number=4, posting_date=2026-04-02, account_code=120000, debit_amount=0.00, credit_amount=3409.00, currency=INR, external_reference=set_0073_0001, narration=Synthetic clearing credit

## PR-011

### GATEWAY

- `PR-011-E01` — gateway_event_id=gwe_0101_000066, event_type=PAYMENT, transaction_id=pay_0101_000066, settlement_id=set_0101_0014, amount_minor=34200, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=captured, reference=order_0101_000066, narration=Synthetic captured payment

- `PR-011-E02` — gateway_event_id=gwe_0101_000067, event_type=PAYMENT, transaction_id=pay_0101_000067, settlement_id=set_0101_0014, amount_minor=167100, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=captured, reference=order_0101_000067, narration=Synthetic captured payment

- `PR-011-E03` — gateway_event_id=gwe_0101_000068, event_type=PAYMENT, transaction_id=pay_0101_000068, settlement_id=set_0101_0014, amount_minor=108400, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=captured, reference=order_0101_000068, narration=Synthetic captured payment

- `PR-011-E04` — gateway_event_id=gwe_0101_000069, event_type=PAYMENT, transaction_id=pay_0101_000069, settlement_id=set_0101_0014, amount_minor=28200, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=captured, reference=order_0101_000069, narration=Synthetic captured payment

- `PR-011-E05` — gateway_event_id=gwe_0101_000070, event_type=PAYMENT, transaction_id=pay_0101_000070, settlement_id=set_0101_0014, amount_minor=24600, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=captured, reference=order_0101_000070, narration=Synthetic captured payment

- `PR-011-E06` — gateway_event_id=gwe_fee_0101_0014, event_type=FEE, transaction_id=, settlement_id=set_0101_0014, amount_minor=9388, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=processed, reference=set_0101_0014, narration=Synthetic gateway fee

- `PR-011-E07` — gateway_event_id=gwe_tax_0101_0014, event_type=TAX, transaction_id=, settlement_id=set_0101_0014, amount_minor=1689, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=processed, reference=set_0101_0014, narration=Synthetic GST on gateway fee

- `PR-011-E08` — gateway_event_id=gwe_set_0101_0014, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0101_0014, amount_minor=351423, currency=INR, event_at=2026-04-14T10:00:00+00:00, status=settled, reference=UTR010100000014, narration=Synthetic net settlement

### BANK

- `PR-011-E09` — bank_record_id=bnk_0101_0014, value_date=2026-04-15, booking_date=2026-04-15, credit_amount=3514.23, debit_amount=0.00, utr=UTR010100000014, narration=Synthetic settlement set_0101_0014, currency=INR, account_reference=acct_demo_01

- `PR-011-E10` — bank_record_id=bnk_0101_0014_candidate, value_date=2026-04-15, booking_date=2026-04-15, credit_amount=3514.23, debit_amount=0.00, utr=ALTUTR010100000014, narration=Synthetic equal-amount competing bank candidate, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-011-E11` — journal_id=jrn_0101_0014, line_number=1, posting_date=2026-04-15, account_code=110000, debit_amount=3514.23, credit_amount=0.00, currency=INR, external_reference=set_0101_0014, narration=Synthetic bank receipt

- `PR-011-E12` — journal_id=jrn_0101_0014, line_number=2, posting_date=2026-04-15, account_code=510000, debit_amount=93.88, credit_amount=0.00, currency=INR, external_reference=set_0101_0014, narration=Synthetic gateway fee expense

- `PR-011-E13` — journal_id=jrn_0101_0014, line_number=3, posting_date=2026-04-15, account_code=140000, debit_amount=16.89, credit_amount=0.00, currency=INR, external_reference=set_0101_0014, narration=Synthetic input GST

- `PR-011-E14` — journal_id=jrn_0101_0014, line_number=4, posting_date=2026-04-15, account_code=120000, debit_amount=0.00, credit_amount=3625.00, currency=INR, external_reference=set_0101_0014, narration=Synthetic clearing credit

## PR-012

### GATEWAY

- `PR-012-E01` — gateway_event_id=gwe_0101_000086, event_type=PAYMENT, transaction_id=pay_0101_000086, settlement_id=set_0101_0018, amount_minor=68100, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0101_000086, narration=Synthetic captured payment

- `PR-012-E02` — gateway_event_id=gwe_0101_000087, event_type=PAYMENT, transaction_id=pay_0101_000087, settlement_id=set_0101_0018, amount_minor=26400, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0101_000087, narration=Synthetic captured payment

- `PR-012-E03` — gateway_event_id=gwe_0101_000088, event_type=PAYMENT, transaction_id=pay_0101_000088, settlement_id=set_0101_0018, amount_minor=138700, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0101_000088, narration=Synthetic captured payment

- `PR-012-E04` — gateway_event_id=gwe_0101_000089, event_type=PAYMENT, transaction_id=pay_0101_000089, settlement_id=set_0101_0018, amount_minor=79300, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0101_000089, narration=Synthetic captured payment

- `PR-012-E05` — gateway_event_id=gwe_0101_000090, event_type=PAYMENT, transaction_id=pay_0101_000090, settlement_id=set_0101_0018, amount_minor=94900, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=captured, reference=order_0101_000090, narration=Synthetic captured payment

- `PR-012-E06` — gateway_event_id=gwe_fee_0101_0018, event_type=FEE, transaction_id=, settlement_id=set_0101_0018, amount_minor=10551, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=processed, reference=set_0101_0018, narration=Synthetic gateway fee

- `PR-012-E07` — gateway_event_id=gwe_tax_0101_0018, event_type=TAX, transaction_id=, settlement_id=set_0101_0018, amount_minor=1899, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=processed, reference=set_0101_0018, narration=Synthetic GST on gateway fee

- `PR-012-E08` — gateway_event_id=gwe_set_0101_0018, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0101_0018, amount_minor=394950, currency=INR, event_at=2026-04-18T10:00:00+00:00, status=settled, reference=UTR010100000018, narration=Synthetic net settlement

### BANK

- `PR-012-E09` — bank_record_id=bnk_0101_0018, value_date=2026-04-19, booking_date=2026-04-19, credit_amount=3949.50, debit_amount=0.00, utr=UTR010100000018, narration=Synthetic settlement set_0101_0018, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-012-E10` — journal_id=jrn_0101_0018, line_number=1, posting_date=2026-04-19, account_code=110000, debit_amount=3950.49, credit_amount=0.00, currency=INR, external_reference=set_0101_0018, narration=Synthetic bank receipt

- `PR-012-E11` — journal_id=jrn_0101_0018, line_number=2, posting_date=2026-04-19, account_code=510000, debit_amount=105.51, credit_amount=0.00, currency=INR, external_reference=set_0101_0018, narration=Synthetic gateway fee expense

- `PR-012-E12` — journal_id=jrn_0101_0018, line_number=3, posting_date=2026-04-19, account_code=140000, debit_amount=18.99, credit_amount=0.00, currency=INR, external_reference=set_0101_0018, narration=Synthetic input GST

- `PR-012-E13` — journal_id=jrn_0101_0018, line_number=4, posting_date=2026-04-19, account_code=120000, debit_amount=0.00, credit_amount=4074.00, currency=INR, external_reference=set_0101_0018, narration=Synthetic clearing credit

## PR-013

### GATEWAY

- `PR-013-E01` — gateway_event_id=gwe_0101_000091, event_type=PAYMENT, transaction_id=pay_0101_000091, settlement_id=set_0101_0019, amount_minor=118900, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=captured, reference=order_0101_000091, narration=Synthetic captured payment

- `PR-013-E02` — gateway_event_id=gwe_0101_000092, event_type=PAYMENT, transaction_id=pay_0101_000092, settlement_id=set_0101_0019, amount_minor=74400, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=captured, reference=order_0101_000092, narration=Synthetic captured payment

- `PR-013-E03` — gateway_event_id=gwe_0101_000093, event_type=PAYMENT, transaction_id=pay_0101_000093, settlement_id=set_0101_0019, amount_minor=192000, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=captured, reference=order_0101_000093, narration=Synthetic captured payment

- `PR-013-E04` — gateway_event_id=gwe_0101_000094, event_type=PAYMENT, transaction_id=pay_0101_000094, settlement_id=set_0101_0019, amount_minor=163900, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=captured, reference=order_0101_000094, narration=Synthetic captured payment

- `PR-013-E05` — gateway_event_id=gwe_0101_000095, event_type=PAYMENT, transaction_id=pay_0101_000095, settlement_id=set_0101_0019, amount_minor=5300, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=captured, reference=order_0101_000095, narration=Synthetic captured payment

- `PR-013-E06` — gateway_event_id=gwe_fee_0101_0019, event_type=FEE, transaction_id=, settlement_id=set_0101_0019, amount_minor=14084, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=processed, reference=set_0101_0019, narration=Synthetic gateway fee

- `PR-013-E07` — gateway_event_id=gwe_tax_0101_0019, event_type=TAX, transaction_id=, settlement_id=set_0101_0019, amount_minor=2535, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=processed, reference=set_0101_0019, narration=Synthetic GST on gateway fee

- `PR-013-E08` — gateway_event_id=gwe_set_0101_0019, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0101_0019, amount_minor=537881, currency=INR, event_at=2026-04-19T10:00:00+00:00, status=settled, reference=UTR010100000019, narration=Synthetic net settlement

### BANK

- `PR-013-E09` — bank_record_id=bnk_0101_0019, value_date=2026-04-20, booking_date=2026-04-20, credit_amount=5378.81, debit_amount=0.00, utr=UTR01010000001X, narration=Synthetic settlement set_0101_0019, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-013-E10` — journal_id=jrn_0101_0019, line_number=1, posting_date=2026-04-20, account_code=110000, debit_amount=5378.81, credit_amount=0.00, currency=INR, external_reference=set_0101_0019, narration=Synthetic bank receipt

- `PR-013-E11` — journal_id=jrn_0101_0019, line_number=2, posting_date=2026-04-20, account_code=510000, debit_amount=140.84, credit_amount=0.00, currency=INR, external_reference=set_0101_0019, narration=Synthetic gateway fee expense

- `PR-013-E12` — journal_id=jrn_0101_0019, line_number=3, posting_date=2026-04-20, account_code=140000, debit_amount=25.35, credit_amount=0.00, currency=INR, external_reference=set_0101_0019, narration=Synthetic input GST

- `PR-013-E13` — journal_id=jrn_0101_0019, line_number=4, posting_date=2026-04-20, account_code=120000, debit_amount=0.00, credit_amount=5545.00, currency=INR, external_reference=set_0101_0019, narration=Synthetic clearing credit

## PR-014

### GATEWAY

- `PR-014-E01` — gateway_event_id=gwe_0101_000036, event_type=PAYMENT, transaction_id=pay_0101_000036, settlement_id=set_0101_0008, amount_minor=132800, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=captured, reference=order_0101_000036, narration=Synthetic captured payment

- `PR-014-E02` — gateway_event_id=gwe_0101_000037, event_type=PAYMENT, transaction_id=pay_0101_000037, settlement_id=set_0101_0008, amount_minor=173400, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=captured, reference=order_0101_000037, narration=Synthetic captured payment

- `PR-014-E03` — gateway_event_id=gwe_0101_000038, event_type=PAYMENT, transaction_id=pay_0101_000038, settlement_id=set_0101_0008, amount_minor=45300, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=captured, reference=order_0101_000038, narration=Synthetic captured payment

- `PR-014-E04` — gateway_event_id=gwe_0101_000039, event_type=PAYMENT, transaction_id=pay_0101_000039, settlement_id=set_0101_0008, amount_minor=54400, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=captured, reference=order_0101_000039, narration=Synthetic captured payment

- `PR-014-E05` — gateway_event_id=gwe_0101_000040, event_type=PAYMENT, transaction_id=pay_0101_000040, settlement_id=set_0101_0008, amount_minor=16600, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=captured, reference=order_0101_000040, narration=Synthetic captured payment

- `PR-014-E06` — gateway_event_id=gwe_fee_0101_0008, event_type=FEE, transaction_id=, settlement_id=set_0101_0008, amount_minor=8323, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=processed, reference=set_0101_0008, narration=Synthetic gateway fee

- `PR-014-E07` — gateway_event_id=gwe_tax_0101_0008, event_type=TAX, transaction_id=, settlement_id=set_0101_0008, amount_minor=1498, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=processed, reference=set_0101_0008, narration=Synthetic GST on gateway fee

- `PR-014-E08` — gateway_event_id=gwe_set_0101_0008, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0101_0008, amount_minor=412679, currency=INR, event_at=2026-04-08T10:00:00+00:00, status=settled, reference=UTR010100000008, narration=Synthetic net settlement

### BANK

- `PR-014-E09` — bank_record_id=bnk_0101_0008, value_date=2026-04-09, booking_date=2026-04-09, credit_amount=4126.79, debit_amount=0.00, utr=UTR010100000008, narration=Synthetic settlement set_0101_0008, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-014-E10` — journal_id=jrn_0101_0008, line_number=1, posting_date=2026-04-09, account_code=110000, debit_amount=4126.79, credit_amount=0.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic bank receipt

- `PR-014-E11` — journal_id=jrn_0101_0008, line_number=2, posting_date=2026-04-09, account_code=510000, debit_amount=83.23, credit_amount=0.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic gateway fee expense

- `PR-014-E12` — journal_id=jrn_0101_0008, line_number=3, posting_date=2026-04-09, account_code=140000, debit_amount=14.98, credit_amount=0.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic input GST

- `PR-014-E13` — journal_id=jrn_0101_0008, line_number=4, posting_date=2026-04-09, account_code=120000, debit_amount=0.00, credit_amount=4225.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic clearing credit

- `PR-014-E14` — journal_id=jrn_0101_0008_duplicate, line_number=1, posting_date=2026-04-09, account_code=110000, debit_amount=4126.79, credit_amount=0.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic bank receipt duplicate posting

- `PR-014-E15` — journal_id=jrn_0101_0008_duplicate, line_number=2, posting_date=2026-04-09, account_code=510000, debit_amount=83.23, credit_amount=0.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic gateway fee expense duplicate posting

- `PR-014-E16` — journal_id=jrn_0101_0008_duplicate, line_number=3, posting_date=2026-04-09, account_code=140000, debit_amount=14.98, credit_amount=0.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic input GST duplicate posting

- `PR-014-E17` — journal_id=jrn_0101_0008_duplicate, line_number=4, posting_date=2026-04-09, account_code=120000, debit_amount=0.00, credit_amount=4225.00, currency=INR, external_reference=set_0101_0008, narration=Synthetic clearing credit duplicate posting

## PR-015

### GATEWAY

- `PR-015-E01` — gateway_event_id=gwe_0101_000001, event_type=PAYMENT, transaction_id=pay_0101_000001, settlement_id=set_0101_0001, amount_minor=91700, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0101_000001, narration=Synthetic captured payment

- `PR-015-E02` — gateway_event_id=gwe_0101_000002, event_type=PAYMENT, transaction_id=pay_0101_000002, settlement_id=set_0101_0001, amount_minor=56200, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0101_000002, narration=Synthetic captured payment

- `PR-015-E03` — gateway_event_id=gwe_0101_000003, event_type=PAYMENT, transaction_id=pay_0101_000003, settlement_id=set_0101_0001, amount_minor=184000, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0101_000003, narration=Synthetic captured payment

- `PR-015-E04` — gateway_event_id=gwe_0101_000004, event_type=PAYMENT, transaction_id=pay_0101_000004, settlement_id=set_0101_0001, amount_minor=76200, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0101_000004, narration=Synthetic captured payment

- `PR-015-E05` — gateway_event_id=gwe_0101_000005, event_type=PAYMENT, transaction_id=pay_0101_000005, settlement_id=set_0101_0001, amount_minor=134900, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0101_000005, narration=Synthetic captured payment

- `PR-015-E06` — gateway_event_id=gwe_fee_0101_0001, event_type=FEE, transaction_id=, settlement_id=set_0101_0001, amount_minor=14063, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0101_0001, narration=Synthetic gateway fee

- `PR-015-E07` — gateway_event_id=gwe_tax_0101_0001, event_type=TAX, transaction_id=, settlement_id=set_0101_0001, amount_minor=2531, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0101_0001, narration=Synthetic GST on gateway fee

- `PR-015-E08` — gateway_event_id=gwe_set_0101_0001, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0101_0001, amount_minor=526406, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=settled, reference=UTR010100000001, narration=Synthetic net settlement

### BANK

- `PR-015-E09` — bank_record_id=bnk_0101_0001, value_date=2026-04-02, booking_date=2026-04-02, credit_amount=5264.06, debit_amount=0.00, utr=UTR010100000001, narration=Synthetic settlement set_0101_0001, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-015-E10` — journal_id=jrn_0101_0001, line_number=1, posting_date=2026-04-02, account_code=110000, debit_amount=5264.06, credit_amount=0.00, currency=INR, external_reference=set_0101_0001, narration=Synthetic bank receipt

- `PR-015-E11` — journal_id=jrn_0101_0001, line_number=2, posting_date=2026-04-02, account_code=510000, debit_amount=140.63, credit_amount=0.00, currency=INR, external_reference=set_0101_0001, narration=Synthetic gateway fee expense

- `PR-015-E12` — journal_id=jrn_0101_0001, line_number=3, posting_date=2026-04-02, account_code=140000, debit_amount=25.31, credit_amount=0.00, currency=INR, external_reference=set_0101_0001, narration=Synthetic input GST

- `PR-015-E13` — journal_id=jrn_0101_0001, line_number=4, posting_date=2026-04-02, account_code=120000, debit_amount=0.00, credit_amount=5430.00, currency=INR, external_reference=set_0101_0001, narration=Synthetic clearing credit

## PR-016

### GATEWAY

- `PR-016-E01` — gateway_event_id=gwe_0211_000026, event_type=PAYMENT, transaction_id=pay_0211_000026, settlement_id=set_0211_0006, amount_minor=46500, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=captured, reference=order_0211_000026, narration=Synthetic captured payment

- `PR-016-E02` — gateway_event_id=gwe_0211_000027, event_type=PAYMENT, transaction_id=pay_0211_000027, settlement_id=set_0211_0006, amount_minor=21500, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=captured, reference=order_0211_000027, narration=Synthetic captured payment

- `PR-016-E03` — gateway_event_id=gwe_0211_000028, event_type=PAYMENT, transaction_id=pay_0211_000028, settlement_id=set_0211_0006, amount_minor=178300, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=captured, reference=order_0211_000028, narration=Synthetic captured payment

- `PR-016-E04` — gateway_event_id=gwe_0211_000029, event_type=PAYMENT, transaction_id=pay_0211_000029, settlement_id=set_0211_0006, amount_minor=35800, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=captured, reference=order_0211_000029, narration=Synthetic captured payment

- `PR-016-E05` — gateway_event_id=gwe_0211_000030, event_type=PAYMENT, transaction_id=pay_0211_000030, settlement_id=set_0211_0006, amount_minor=29600, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=captured, reference=order_0211_000030, narration=Synthetic captured payment

- `PR-016-E06` — gateway_event_id=gwe_fee_0211_0006, event_type=FEE, transaction_id=, settlement_id=set_0211_0006, amount_minor=7044, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=processed, reference=set_0211_0006, narration=Synthetic gateway fee

- `PR-016-E07` — gateway_event_id=gwe_tax_0211_0006, event_type=TAX, transaction_id=, settlement_id=set_0211_0006, amount_minor=1267, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=processed, reference=set_0211_0006, narration=Synthetic GST on gateway fee

- `PR-016-E08` — gateway_event_id=gwe_set_0211_0006, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0211_0006, amount_minor=303389, currency=INR, event_at=2026-04-06T10:00:00+00:00, status=settled, reference=UTR021100000006, narration=Synthetic net settlement

### BANK

- `PR-016-E09` — bank_record_id=bnk_0211_0006, value_date=2026-04-07, booking_date=2026-04-07, credit_amount=3033.89, debit_amount=0.00, utr=UTR021100000006, narration=Synthetic settlement set_0211_0006, currency=INR, account_reference=acct_demo_01

- `PR-016-E10` — bank_record_id=bnk_0211_0006_candidate, value_date=2026-04-07, booking_date=2026-04-07, credit_amount=3033.89, debit_amount=0.00, utr=ALTUTR021100000006, narration=Synthetic equal-amount competing bank candidate, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-016-E11` — journal_id=jrn_0211_0006, line_number=1, posting_date=2026-04-07, account_code=110000, debit_amount=3033.89, credit_amount=0.00, currency=INR, external_reference=set_0211_0006, narration=Synthetic bank receipt

- `PR-016-E12` — journal_id=jrn_0211_0006, line_number=2, posting_date=2026-04-07, account_code=510000, debit_amount=70.44, credit_amount=0.00, currency=INR, external_reference=set_0211_0006, narration=Synthetic gateway fee expense

- `PR-016-E13` — journal_id=jrn_0211_0006, line_number=3, posting_date=2026-04-07, account_code=140000, debit_amount=12.67, credit_amount=0.00, currency=INR, external_reference=set_0211_0006, narration=Synthetic input GST

- `PR-016-E14` — journal_id=jrn_0211_0006, line_number=4, posting_date=2026-04-07, account_code=120000, debit_amount=0.00, credit_amount=3117.00, currency=INR, external_reference=set_0211_0006, narration=Synthetic clearing credit

## PR-017

### GATEWAY

- `PR-017-E01` — gateway_event_id=gwe_0211_000081, event_type=PAYMENT, transaction_id=pay_0211_000081, settlement_id=set_0211_0017, amount_minor=53800, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=captured, reference=order_0211_000081, narration=Synthetic captured payment

- `PR-017-E02` — gateway_event_id=gwe_0211_000082, event_type=PAYMENT, transaction_id=pay_0211_000082, settlement_id=set_0211_0017, amount_minor=87900, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=captured, reference=order_0211_000082, narration=Synthetic captured payment

- `PR-017-E03` — gateway_event_id=gwe_0211_000083, event_type=PAYMENT, transaction_id=pay_0211_000083, settlement_id=set_0211_0017, amount_minor=26900, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=captured, reference=order_0211_000083, narration=Synthetic captured payment

- `PR-017-E04` — gateway_event_id=gwe_0211_000084, event_type=PAYMENT, transaction_id=pay_0211_000084, settlement_id=set_0211_0017, amount_minor=184400, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=captured, reference=order_0211_000084, narration=Synthetic captured payment

- `PR-017-E05` — gateway_event_id=gwe_0211_000085, event_type=PAYMENT, transaction_id=pay_0211_000085, settlement_id=set_0211_0017, amount_minor=175600, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=captured, reference=order_0211_000085, narration=Synthetic captured payment

- `PR-017-E06` — gateway_event_id=gwe_fee_0211_0017, event_type=FEE, transaction_id=, settlement_id=set_0211_0017, amount_minor=11576, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=processed, reference=set_0211_0017, narration=Synthetic gateway fee

- `PR-017-E07` — gateway_event_id=gwe_tax_0211_0017, event_type=TAX, transaction_id=, settlement_id=set_0211_0017, amount_minor=2083, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=processed, reference=set_0211_0017, narration=Synthetic GST on gateway fee

- `PR-017-E08` — gateway_event_id=gwe_set_0211_0017, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0211_0017, amount_minor=514941, currency=INR, event_at=2026-04-17T10:00:00+00:00, status=settled, reference=UTR021100000017, narration=Synthetic net settlement

### BANK

- `PR-017-E09` — bank_record_id=bnk_0211_0017, value_date=2026-04-18, booking_date=2026-04-18, credit_amount=5149.41, debit_amount=0.00, utr=UTR021100000017, narration=Synthetic settlement set_0211_0017, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-017-E10` — journal_id=jrn_0211_0017, line_number=1, posting_date=2026-04-18, account_code=110000, debit_amount=5150.40, credit_amount=0.00, currency=INR, external_reference=set_0211_0017, narration=Synthetic bank receipt

- `PR-017-E11` — journal_id=jrn_0211_0017, line_number=2, posting_date=2026-04-18, account_code=510000, debit_amount=115.76, credit_amount=0.00, currency=INR, external_reference=set_0211_0017, narration=Synthetic gateway fee expense

- `PR-017-E12` — journal_id=jrn_0211_0017, line_number=3, posting_date=2026-04-18, account_code=140000, debit_amount=20.83, credit_amount=0.00, currency=INR, external_reference=set_0211_0017, narration=Synthetic input GST

- `PR-017-E13` — journal_id=jrn_0211_0017, line_number=4, posting_date=2026-04-18, account_code=120000, debit_amount=0.00, credit_amount=5286.00, currency=INR, external_reference=set_0211_0017, narration=Synthetic clearing credit

## PR-018

### GATEWAY

- `PR-018-E01` — gateway_event_id=gwe_0211_000031, event_type=PAYMENT, transaction_id=pay_0211_000031, settlement_id=set_0211_0007, amount_minor=131900, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0211_000031, narration=Synthetic captured payment

- `PR-018-E02` — gateway_event_id=gwe_0211_000032, event_type=PAYMENT, transaction_id=pay_0211_000032, settlement_id=set_0211_0007, amount_minor=7900, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0211_000032, narration=Synthetic captured payment

- `PR-018-E03` — gateway_event_id=gwe_0211_000033, event_type=PAYMENT, transaction_id=pay_0211_000033, settlement_id=set_0211_0007, amount_minor=53800, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0211_000033, narration=Synthetic captured payment

- `PR-018-E04` — gateway_event_id=gwe_0211_000034, event_type=PAYMENT, transaction_id=pay_0211_000034, settlement_id=set_0211_0007, amount_minor=5700, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0211_000034, narration=Synthetic captured payment

- `PR-018-E05` — gateway_event_id=gwe_0211_000035, event_type=PAYMENT, transaction_id=pay_0211_000035, settlement_id=set_0211_0007, amount_minor=95500, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=captured, reference=order_0211_000035, narration=Synthetic captured payment

- `PR-018-E06` — gateway_event_id=gwe_fee_0211_0007, event_type=FEE, transaction_id=, settlement_id=set_0211_0007, amount_minor=6721, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=processed, reference=set_0211_0007, narration=Synthetic gateway fee

- `PR-018-E07` — gateway_event_id=gwe_tax_0211_0007, event_type=TAX, transaction_id=, settlement_id=set_0211_0007, amount_minor=1209, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=processed, reference=set_0211_0007, narration=Synthetic GST on gateway fee

- `PR-018-E08` — gateway_event_id=gwe_set_0211_0007, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0211_0007, amount_minor=286870, currency=INR, event_at=2026-04-07T10:00:00+00:00, status=settled, reference=UTR021100000007, narration=Synthetic net settlement

### BANK

No source row is present.

### ERP

- `PR-018-E09` — journal_id=jrn_0211_0007, line_number=1, posting_date=2026-04-08, account_code=110000, debit_amount=2868.70, credit_amount=0.00, currency=INR, external_reference=set_0211_0007, narration=Synthetic bank receipt

- `PR-018-E10` — journal_id=jrn_0211_0007, line_number=2, posting_date=2026-04-08, account_code=510000, debit_amount=67.21, credit_amount=0.00, currency=INR, external_reference=set_0211_0007, narration=Synthetic gateway fee expense

- `PR-018-E11` — journal_id=jrn_0211_0007, line_number=3, posting_date=2026-04-08, account_code=140000, debit_amount=12.09, credit_amount=0.00, currency=INR, external_reference=set_0211_0007, narration=Synthetic input GST

- `PR-018-E12` — journal_id=jrn_0211_0007, line_number=4, posting_date=2026-04-08, account_code=120000, debit_amount=0.00, credit_amount=2948.00, currency=INR, external_reference=set_0211_0007, narration=Synthetic clearing credit

## PR-019

### GATEWAY

- `PR-019-E01` — gateway_event_id=gwe_0211_000041, event_type=PAYMENT, transaction_id=pay_0211_000041, settlement_id=set_0211_0009, amount_minor=81100, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0211_000041, narration=Synthetic captured payment

- `PR-019-E02` — gateway_event_id=gwe_0211_000042, event_type=PAYMENT, transaction_id=pay_0211_000042, settlement_id=set_0211_0009, amount_minor=179600, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0211_000042, narration=Synthetic captured payment

- `PR-019-E03` — gateway_event_id=gwe_0211_000043, event_type=PAYMENT, transaction_id=pay_0211_000043, settlement_id=set_0211_0009, amount_minor=26400, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0211_000043, narration=Synthetic captured payment

- `PR-019-E04` — gateway_event_id=gwe_0211_000044, event_type=PAYMENT, transaction_id=pay_0211_000044, settlement_id=set_0211_0009, amount_minor=11700, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0211_000044, narration=Synthetic captured payment

- `PR-019-E05` — gateway_event_id=gwe_0211_000045, event_type=PAYMENT, transaction_id=pay_0211_000045, settlement_id=set_0211_0009, amount_minor=129700, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=captured, reference=order_0211_000045, narration=Synthetic captured payment

- `PR-019-E06` — gateway_event_id=gwe_fee_0211_0009, event_type=FEE, transaction_id=, settlement_id=set_0211_0009, amount_minor=8055, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=processed, reference=set_0211_0009, narration=Synthetic gateway fee

- `PR-019-E07` — gateway_event_id=gwe_tax_0211_0009, event_type=TAX, transaction_id=, settlement_id=set_0211_0009, amount_minor=1449, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=processed, reference=set_0211_0009, narration=Synthetic GST on gateway fee

- `PR-019-E08` — gateway_event_id=gwe_set_0211_0009, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0211_0009, amount_minor=418996, currency=INR, event_at=2026-04-09T10:00:00+00:00, status=settled, reference=UTR021100000009, narration=Synthetic net settlement

### BANK

- `PR-019-E09` — bank_record_id=bnk_0211_0009, value_date=2026-04-10, booking_date=2026-04-10, credit_amount=4189.96, debit_amount=0.00, utr=UTR021100000009, narration=Synthetic settlement set_0211_0009, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-019-E10` — journal_id=jrn_0211_0009, line_number=1, posting_date=2026-04-10, account_code=110000, debit_amount=4189.96, credit_amount=0.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic bank receipt

- `PR-019-E11` — journal_id=jrn_0211_0009, line_number=2, posting_date=2026-04-10, account_code=510000, debit_amount=80.55, credit_amount=0.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic gateway fee expense

- `PR-019-E12` — journal_id=jrn_0211_0009, line_number=3, posting_date=2026-04-10, account_code=140000, debit_amount=14.49, credit_amount=0.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic input GST

- `PR-019-E13` — journal_id=jrn_0211_0009, line_number=4, posting_date=2026-04-10, account_code=120000, debit_amount=0.00, credit_amount=4285.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic clearing credit

- `PR-019-E14` — journal_id=jrn_0211_0009_duplicate, line_number=1, posting_date=2026-04-10, account_code=110000, debit_amount=4189.96, credit_amount=0.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic bank receipt duplicate posting

- `PR-019-E15` — journal_id=jrn_0211_0009_duplicate, line_number=2, posting_date=2026-04-10, account_code=510000, debit_amount=80.55, credit_amount=0.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic gateway fee expense duplicate posting

- `PR-019-E16` — journal_id=jrn_0211_0009_duplicate, line_number=3, posting_date=2026-04-10, account_code=140000, debit_amount=14.49, credit_amount=0.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic input GST duplicate posting

- `PR-019-E17` — journal_id=jrn_0211_0009_duplicate, line_number=4, posting_date=2026-04-10, account_code=120000, debit_amount=0.00, credit_amount=4285.00, currency=INR, external_reference=set_0211_0009, narration=Synthetic clearing credit duplicate posting

## PR-020

### GATEWAY

- `PR-020-E01` — gateway_event_id=gwe_0211_000001, event_type=PAYMENT, transaction_id=pay_0211_000001, settlement_id=set_0211_0001, amount_minor=45900, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0211_000001, narration=Synthetic captured payment

- `PR-020-E02` — gateway_event_id=gwe_0211_000002, event_type=PAYMENT, transaction_id=pay_0211_000002, settlement_id=set_0211_0001, amount_minor=26600, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0211_000002, narration=Synthetic captured payment

- `PR-020-E03` — gateway_event_id=gwe_0211_000003, event_type=PAYMENT, transaction_id=pay_0211_000003, settlement_id=set_0211_0001, amount_minor=141700, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0211_000003, narration=Synthetic captured payment

- `PR-020-E04` — gateway_event_id=gwe_0211_000004, event_type=PAYMENT, transaction_id=pay_0211_000004, settlement_id=set_0211_0001, amount_minor=165900, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0211_000004, narration=Synthetic captured payment

- `PR-020-E05` — gateway_event_id=gwe_0211_000005, event_type=PAYMENT, transaction_id=pay_0211_000005, settlement_id=set_0211_0001, amount_minor=17200, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0211_000005, narration=Synthetic captured payment

- `PR-020-E06` — gateway_event_id=gwe_fee_0211_0001, event_type=FEE, transaction_id=, settlement_id=set_0211_0001, amount_minor=8541, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0211_0001, narration=Synthetic gateway fee

- `PR-020-E07` — gateway_event_id=gwe_tax_0211_0001, event_type=TAX, transaction_id=, settlement_id=set_0211_0001, amount_minor=1537, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0211_0001, narration=Synthetic GST on gateway fee

- `PR-020-E08` — gateway_event_id=gwe_set_0211_0001, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0211_0001, amount_minor=387222, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=settled, reference=UTR021100000001, narration=Synthetic net settlement

### BANK

- `PR-020-E09` — bank_record_id=bnk_0211_0001, value_date=2026-04-02, booking_date=2026-04-02, credit_amount=3872.22, debit_amount=0.00, utr=UTR021100000001, narration=Synthetic settlement set_0211_0001, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-020-E10` — journal_id=jrn_0211_0001, line_number=1, posting_date=2026-04-02, account_code=110000, debit_amount=3872.22, credit_amount=0.00, currency=INR, external_reference=set_0211_0001, narration=Synthetic bank receipt

- `PR-020-E11` — journal_id=jrn_0211_0001, line_number=2, posting_date=2026-04-02, account_code=510000, debit_amount=85.41, credit_amount=0.00, currency=INR, external_reference=set_0211_0001, narration=Synthetic gateway fee expense

- `PR-020-E12` — journal_id=jrn_0211_0001, line_number=3, posting_date=2026-04-02, account_code=140000, debit_amount=15.37, credit_amount=0.00, currency=INR, external_reference=set_0211_0001, narration=Synthetic input GST

- `PR-020-E13` — journal_id=jrn_0211_0001, line_number=4, posting_date=2026-04-02, account_code=120000, debit_amount=0.00, credit_amount=3973.00, currency=INR, external_reference=set_0211_0001, narration=Synthetic clearing credit

## PR-021

### GATEWAY

- `PR-021-E01` — gateway_event_id=gwe_0307_000051, event_type=PAYMENT, transaction_id=pay_0307_000051, settlement_id=set_0307_0011, amount_minor=94700, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=captured, reference=order_0307_000051, narration=Synthetic captured payment

- `PR-021-E02` — gateway_event_id=gwe_0307_000052, event_type=PAYMENT, transaction_id=pay_0307_000052, settlement_id=set_0307_0011, amount_minor=198800, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=captured, reference=order_0307_000052, narration=Synthetic captured payment

- `PR-021-E03` — gateway_event_id=gwe_0307_000053, event_type=PAYMENT, transaction_id=pay_0307_000053, settlement_id=set_0307_0011, amount_minor=115300, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=captured, reference=order_0307_000053, narration=Synthetic captured payment

- `PR-021-E04` — gateway_event_id=gwe_0307_000054, event_type=PAYMENT, transaction_id=pay_0307_000054, settlement_id=set_0307_0011, amount_minor=156800, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=captured, reference=order_0307_000054, narration=Synthetic captured payment

- `PR-021-E05` — gateway_event_id=gwe_0307_000055, event_type=PAYMENT, transaction_id=pay_0307_000055, settlement_id=set_0307_0011, amount_minor=120000, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=captured, reference=order_0307_000055, narration=Synthetic captured payment

- `PR-021-E06` — gateway_event_id=gwe_fee_0307_0011, event_type=FEE, transaction_id=, settlement_id=set_0307_0011, amount_minor=16180, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=processed, reference=set_0307_0011, narration=Synthetic gateway fee

- `PR-021-E07` — gateway_event_id=gwe_tax_0307_0011, event_type=TAX, transaction_id=, settlement_id=set_0307_0011, amount_minor=2912, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=processed, reference=set_0307_0011, narration=Synthetic GST on gateway fee

- `PR-021-E08` — gateway_event_id=gwe_set_0307_0011, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0307_0011, amount_minor=666508, currency=INR, event_at=2026-04-11T10:00:00+00:00, status=settled, reference=UTR030700000011, narration=Synthetic net settlement

### BANK

- `PR-021-E09` — bank_record_id=bnk_0307_0011, value_date=2026-04-12, booking_date=2026-04-12, credit_amount=6665.08, debit_amount=0.00, utr=UTR030700000011, narration=Synthetic settlement set_0307_0011, currency=INR, account_reference=acct_demo_01

- `PR-021-E10` — bank_record_id=bnk_0307_0011_candidate, value_date=2026-04-12, booking_date=2026-04-12, credit_amount=6665.08, debit_amount=0.00, utr=ALTUTR030700000011, narration=Synthetic equal-amount competing bank candidate, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-021-E11` — journal_id=jrn_0307_0011, line_number=1, posting_date=2026-04-12, account_code=110000, debit_amount=6665.08, credit_amount=0.00, currency=INR, external_reference=set_0307_0011, narration=Synthetic bank receipt

- `PR-021-E12` — journal_id=jrn_0307_0011, line_number=2, posting_date=2026-04-12, account_code=510000, debit_amount=161.80, credit_amount=0.00, currency=INR, external_reference=set_0307_0011, narration=Synthetic gateway fee expense

- `PR-021-E13` — journal_id=jrn_0307_0011, line_number=3, posting_date=2026-04-12, account_code=140000, debit_amount=29.12, credit_amount=0.00, currency=INR, external_reference=set_0307_0011, narration=Synthetic input GST

- `PR-021-E14` — journal_id=jrn_0307_0011, line_number=4, posting_date=2026-04-12, account_code=120000, debit_amount=0.00, credit_amount=6856.00, currency=INR, external_reference=set_0307_0011, narration=Synthetic clearing credit

## PR-022

### GATEWAY

- `PR-022-E01` — gateway_event_id=gwe_0307_000056, event_type=PAYMENT, transaction_id=pay_0307_000056, settlement_id=set_0307_0012, amount_minor=190700, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=captured, reference=order_0307_000056, narration=Synthetic captured payment

- `PR-022-E02` — gateway_event_id=gwe_0307_000057, event_type=PAYMENT, transaction_id=pay_0307_000057, settlement_id=set_0307_0012, amount_minor=185800, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=captured, reference=order_0307_000057, narration=Synthetic captured payment

- `PR-022-E03` — gateway_event_id=gwe_0307_000058, event_type=PAYMENT, transaction_id=pay_0307_000058, settlement_id=set_0307_0012, amount_minor=51600, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=captured, reference=order_0307_000058, narration=Synthetic captured payment

- `PR-022-E04` — gateway_event_id=gwe_0307_000059, event_type=PAYMENT, transaction_id=pay_0307_000059, settlement_id=set_0307_0012, amount_minor=181600, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=captured, reference=order_0307_000059, narration=Synthetic captured payment

- `PR-022-E05` — gateway_event_id=gwe_0307_000060, event_type=PAYMENT, transaction_id=pay_0307_000060, settlement_id=set_0307_0012, amount_minor=125100, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=captured, reference=order_0307_000060, narration=Synthetic captured payment

- `PR-022-E06` — gateway_event_id=gwe_fee_0307_0012, event_type=FEE, transaction_id=, settlement_id=set_0307_0012, amount_minor=13373, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=processed, reference=set_0307_0012, narration=Synthetic gateway fee

- `PR-022-E07` — gateway_event_id=gwe_tax_0307_0012, event_type=TAX, transaction_id=, settlement_id=set_0307_0012, amount_minor=2407, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=processed, reference=set_0307_0012, narration=Synthetic GST on gateway fee

- `PR-022-E08` — gateway_event_id=gwe_set_0307_0012, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0307_0012, amount_minor=719020, currency=INR, event_at=2026-04-12T10:00:00+00:00, status=settled, reference=UTR030700000012, narration=Synthetic net settlement

### BANK

- `PR-022-E09` — bank_record_id=bnk_0307_0012, value_date=2026-04-13, booking_date=2026-04-13, credit_amount=7190.20, debit_amount=0.00, utr=UTR030700000012, narration=Synthetic settlement set_0307_0012, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-022-E10` — journal_id=jrn_0307_0012, line_number=1, posting_date=2026-04-13, account_code=110000, debit_amount=7191.19, credit_amount=0.00, currency=INR, external_reference=set_0307_0012, narration=Synthetic bank receipt

- `PR-022-E11` — journal_id=jrn_0307_0012, line_number=2, posting_date=2026-04-13, account_code=510000, debit_amount=133.73, credit_amount=0.00, currency=INR, external_reference=set_0307_0012, narration=Synthetic gateway fee expense

- `PR-022-E12` — journal_id=jrn_0307_0012, line_number=3, posting_date=2026-04-13, account_code=140000, debit_amount=24.07, credit_amount=0.00, currency=INR, external_reference=set_0307_0012, narration=Synthetic input GST

- `PR-022-E13` — journal_id=jrn_0307_0012, line_number=4, posting_date=2026-04-13, account_code=120000, debit_amount=0.00, credit_amount=7348.00, currency=INR, external_reference=set_0307_0012, narration=Synthetic clearing credit

## PR-023

### GATEWAY

- `PR-023-E01` — gateway_event_id=gwe_0307_000076, event_type=PAYMENT, transaction_id=pay_0307_000076, settlement_id=set_0307_0016, amount_minor=15500, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=captured, reference=order_0307_000076, narration=Synthetic captured payment

- `PR-023-E02` — gateway_event_id=gwe_0307_000077, event_type=PAYMENT, transaction_id=pay_0307_000077, settlement_id=set_0307_0016, amount_minor=21200, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=captured, reference=order_0307_000077, narration=Synthetic captured payment

- `PR-023-E03` — gateway_event_id=gwe_0307_000078, event_type=PAYMENT, transaction_id=pay_0307_000078, settlement_id=set_0307_0016, amount_minor=48000, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=captured, reference=order_0307_000078, narration=Synthetic captured payment

- `PR-023-E04` — gateway_event_id=gwe_0307_000079, event_type=PAYMENT, transaction_id=pay_0307_000079, settlement_id=set_0307_0016, amount_minor=123700, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=captured, reference=order_0307_000079, narration=Synthetic captured payment

- `PR-023-E05` — gateway_event_id=gwe_0307_000080, event_type=PAYMENT, transaction_id=pay_0307_000080, settlement_id=set_0307_0016, amount_minor=57600, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=captured, reference=order_0307_000080, narration=Synthetic captured payment

- `PR-023-E06` — gateway_event_id=gwe_fee_0307_0016, event_type=FEE, transaction_id=, settlement_id=set_0307_0016, amount_minor=6623, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=processed, reference=set_0307_0016, narration=Synthetic gateway fee

- `PR-023-E07` — gateway_event_id=gwe_tax_0307_0016, event_type=TAX, transaction_id=, settlement_id=set_0307_0016, amount_minor=1192, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=processed, reference=set_0307_0016, narration=Synthetic GST on gateway fee

- `PR-023-E08` — gateway_event_id=gwe_set_0307_0016, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0307_0016, amount_minor=258185, currency=INR, event_at=2026-04-16T10:00:00+00:00, status=settled, reference=UTR030700000016, narration=Synthetic net settlement

### BANK

No source row is present.

### ERP

- `PR-023-E09` — journal_id=jrn_0307_0016, line_number=1, posting_date=2026-04-17, account_code=110000, debit_amount=2581.85, credit_amount=0.00, currency=INR, external_reference=set_0307_0016, narration=Synthetic bank receipt

- `PR-023-E10` — journal_id=jrn_0307_0016, line_number=2, posting_date=2026-04-17, account_code=510000, debit_amount=66.23, credit_amount=0.00, currency=INR, external_reference=set_0307_0016, narration=Synthetic gateway fee expense

- `PR-023-E11` — journal_id=jrn_0307_0016, line_number=3, posting_date=2026-04-17, account_code=140000, debit_amount=11.92, credit_amount=0.00, currency=INR, external_reference=set_0307_0016, narration=Synthetic input GST

- `PR-023-E12` — journal_id=jrn_0307_0016, line_number=4, posting_date=2026-04-17, account_code=120000, debit_amount=0.00, credit_amount=2660.00, currency=INR, external_reference=set_0307_0016, narration=Synthetic clearing credit

## PR-024

### GATEWAY

- `PR-024-E01` — gateway_event_id=gwe_0307_000021, event_type=PAYMENT, transaction_id=pay_0307_000021, settlement_id=set_0307_0005, amount_minor=117200, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0307_000021, narration=Synthetic captured payment

- `PR-024-E02` — gateway_event_id=gwe_0307_000022, event_type=PAYMENT, transaction_id=pay_0307_000022, settlement_id=set_0307_0005, amount_minor=151900, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0307_000022, narration=Synthetic captured payment

- `PR-024-E03` — gateway_event_id=gwe_0307_000023, event_type=PAYMENT, transaction_id=pay_0307_000023, settlement_id=set_0307_0005, amount_minor=174500, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0307_000023, narration=Synthetic captured payment

- `PR-024-E04` — gateway_event_id=gwe_0307_000024, event_type=PAYMENT, transaction_id=pay_0307_000024, settlement_id=set_0307_0005, amount_minor=172000, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0307_000024, narration=Synthetic captured payment

- `PR-024-E05` — gateway_event_id=gwe_0307_000025, event_type=PAYMENT, transaction_id=pay_0307_000025, settlement_id=set_0307_0005, amount_minor=90800, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=captured, reference=order_0307_000025, narration=Synthetic captured payment

- `PR-024-E06` — gateway_event_id=gwe_fee_0307_0005, event_type=FEE, transaction_id=, settlement_id=set_0307_0005, amount_minor=16741, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=processed, reference=set_0307_0005, narration=Synthetic gateway fee

- `PR-024-E07` — gateway_event_id=gwe_tax_0307_0005, event_type=TAX, transaction_id=, settlement_id=set_0307_0005, amount_minor=3013, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=processed, reference=set_0307_0005, narration=Synthetic GST on gateway fee

- `PR-024-E08` — gateway_event_id=gwe_set_0307_0005, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0307_0005, amount_minor=686646, currency=INR, event_at=2026-04-05T10:00:00+00:00, status=settled, reference=UTR030700000005, narration=Synthetic net settlement

### BANK

- `PR-024-E09` — bank_record_id=bnk_0307_0005, value_date=2026-04-06, booking_date=2026-04-06, credit_amount=6866.46, debit_amount=0.00, utr=UTR030700000005, narration=Synthetic settlement set_0307_0005, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-024-E10` — journal_id=jrn_0307_0005, line_number=1, posting_date=2026-04-06, account_code=110000, debit_amount=6866.46, credit_amount=0.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic bank receipt

- `PR-024-E11` — journal_id=jrn_0307_0005, line_number=2, posting_date=2026-04-06, account_code=510000, debit_amount=167.41, credit_amount=0.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic gateway fee expense

- `PR-024-E12` — journal_id=jrn_0307_0005, line_number=3, posting_date=2026-04-06, account_code=140000, debit_amount=30.13, credit_amount=0.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic input GST

- `PR-024-E13` — journal_id=jrn_0307_0005, line_number=4, posting_date=2026-04-06, account_code=120000, debit_amount=0.00, credit_amount=7064.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic clearing credit

- `PR-024-E14` — journal_id=jrn_0307_0005_duplicate, line_number=1, posting_date=2026-04-06, account_code=110000, debit_amount=6866.46, credit_amount=0.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic bank receipt duplicate posting

- `PR-024-E15` — journal_id=jrn_0307_0005_duplicate, line_number=2, posting_date=2026-04-06, account_code=510000, debit_amount=167.41, credit_amount=0.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic gateway fee expense duplicate posting

- `PR-024-E16` — journal_id=jrn_0307_0005_duplicate, line_number=3, posting_date=2026-04-06, account_code=140000, debit_amount=30.13, credit_amount=0.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic input GST duplicate posting

- `PR-024-E17` — journal_id=jrn_0307_0005_duplicate, line_number=4, posting_date=2026-04-06, account_code=120000, debit_amount=0.00, credit_amount=7064.00, currency=INR, external_reference=set_0307_0005, narration=Synthetic clearing credit duplicate posting

## PR-025

### GATEWAY

- `PR-025-E01` — gateway_event_id=gwe_0307_000001, event_type=PAYMENT, transaction_id=pay_0307_000001, settlement_id=set_0307_0001, amount_minor=15900, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0307_000001, narration=Synthetic captured payment

- `PR-025-E02` — gateway_event_id=gwe_0307_000002, event_type=PAYMENT, transaction_id=pay_0307_000002, settlement_id=set_0307_0001, amount_minor=13600, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0307_000002, narration=Synthetic captured payment

- `PR-025-E03` — gateway_event_id=gwe_0307_000003, event_type=PAYMENT, transaction_id=pay_0307_000003, settlement_id=set_0307_0001, amount_minor=93000, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0307_000003, narration=Synthetic captured payment

- `PR-025-E04` — gateway_event_id=gwe_0307_000004, event_type=PAYMENT, transaction_id=pay_0307_000004, settlement_id=set_0307_0001, amount_minor=109700, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0307_000004, narration=Synthetic captured payment

- `PR-025-E05` — gateway_event_id=gwe_0307_000005, event_type=PAYMENT, transaction_id=pay_0307_000005, settlement_id=set_0307_0001, amount_minor=146300, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=captured, reference=order_0307_000005, narration=Synthetic captured payment

- `PR-025-E06` — gateway_event_id=gwe_fee_0307_0001, event_type=FEE, transaction_id=, settlement_id=set_0307_0001, amount_minor=7759, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0307_0001, narration=Synthetic gateway fee

- `PR-025-E07` — gateway_event_id=gwe_tax_0307_0001, event_type=TAX, transaction_id=, settlement_id=set_0307_0001, amount_minor=1396, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=processed, reference=set_0307_0001, narration=Synthetic GST on gateway fee

- `PR-025-E08` — gateway_event_id=gwe_set_0307_0001, event_type=SETTLEMENT, transaction_id=, settlement_id=set_0307_0001, amount_minor=369345, currency=INR, event_at=2026-04-01T10:00:00+00:00, status=settled, reference=UTR030700000001, narration=Synthetic net settlement

### BANK

- `PR-025-E09` — bank_record_id=bnk_0307_0001, value_date=2026-04-02, booking_date=2026-04-02, credit_amount=3693.45, debit_amount=0.00, utr=UTR030700000001, narration=Synthetic settlement set_0307_0001, currency=INR, account_reference=acct_demo_01

### ERP

- `PR-025-E10` — journal_id=jrn_0307_0001, line_number=1, posting_date=2026-04-02, account_code=110000, debit_amount=3693.45, credit_amount=0.00, currency=INR, external_reference=set_0307_0001, narration=Synthetic bank receipt

- `PR-025-E11` — journal_id=jrn_0307_0001, line_number=2, posting_date=2026-04-02, account_code=510000, debit_amount=77.59, credit_amount=0.00, currency=INR, external_reference=set_0307_0001, narration=Synthetic gateway fee expense

- `PR-025-E12` — journal_id=jrn_0307_0001, line_number=3, posting_date=2026-04-02, account_code=140000, debit_amount=13.96, credit_amount=0.00, currency=INR, external_reference=set_0307_0001, narration=Synthetic input GST

- `PR-025-E13` — journal_id=jrn_0307_0001, line_number=4, posting_date=2026-04-02, account_code=120000, debit_amount=0.00, credit_amount=3785.00, currency=INR, external_reference=set_0307_0001, narration=Synthetic clearing credit
