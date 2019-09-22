# home-assistant-robart
Home Assistant (custom component) integration of MyVacBot Robart

# Install
- Copy directory **robart** to **.homeassistant/custom_components/**

- Add **vacuum** section to **configuration.yaml**

```
  vacuum:                                                                                                                                      
    - platform: robart                                                                                                                         
      host: <ip address>
```
  
