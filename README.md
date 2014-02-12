AI-Contest-Fremework
====================

### Description
The purpose of this project is to create a contest framework for the AI competition inspired by the Google AI-challenge 2011. The framework will contain a few modules (website, auto-compile system, tournament manager, game engine, and ranking algorithm).

### Goal
The goal of the framework is to provide a framework for the AI competition that can use any game engine follow by the framework specification.

### TODO

- [ ] Write a wiki explaining the architecture and library I plan to use  
- [ ] Write a wiki for protocol definition  
- [ ] Re-structure the project architecture to modularize each components named in description  
- [ ] Implement the website using DJango (Why? Because I want to learn it...)  
- [ ] Implement the basic auto-compile system that takes source code and compile according to the extension name  
- [ ] Implement the basic server that takes the compiled code and execute it  
- [ ] Think of a basic game to play that is not too boring  

## Dependencies:
1. Python 2.7
2. JavaScript for True Skill [Optional]

### Instruction

1. Start tcp-server by
```
python tcpserver.py
```
2. Start web-server and worker by
```
python server.py
```
