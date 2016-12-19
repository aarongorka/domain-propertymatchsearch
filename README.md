# domain-propertymatchsearch
Requirements:
  * python3
  * a modern version of flask (0.11.1 confirmed working)
  * gpxpy

Run with:
```python
python3 domain.py
```

Or build and run the docker image:
```bash
sudo docker build -t domain-propertymatchsearch:latest .
sudo docker run -p 5000:5000 domain-propertymatchsearch
```
