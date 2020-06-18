def consoleHeadder(text=None):
    width = 100
    print('\n'+width*'-'+'\n'+ "---[ " +text+ " ]" +(width - len(text) - 7)*'-'+'\n'+width*'-')
