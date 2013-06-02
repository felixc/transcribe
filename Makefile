test:
	python -m unittest discover test/

sample:
	cd sample; python ../transcribe.py --config sample_config.py

clean-sample:
	rm -rf sample/out

.PHONY: test sample clean-sample
