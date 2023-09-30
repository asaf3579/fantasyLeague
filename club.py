


class club:
    def __init__(self,name,best_score,win_count,lose_count,draw_count,last_three_matches,GF,GA):
        self.name = name
        self.best_score = best_score
        self.win_count = win_count
        self.lose_count = lose_count
        self.draw_count = draw_count
        self.last_three_matches = last_three_matches
        self.GF = GF
        self.GA = GA

    def getScore(self):
        return self.win_count*3 + self.draw_count

    def GetMP(self):
        return self.win_count + self.draw_count + self.lose_count

    def GetGD(self):
        return self.GF-self.GA

    def IncreaseWin(self,GF,GA):
        new_last_three = ['W']
        new_last_three.append(self.last_three_matches[0])
        new_last_three.append(self.last_three_matches[1])
        self.last_three_matches = new_last_three
        self.win_count+=1
        self.GF+=GF
        self.GA+=GA

    def IncreaseLose(self,GF,GA):
        new_last_three = ['L']
        new_last_three.append(self.last_three_matches[0])
        new_last_three.append(self.last_three_matches[1])
        self.last_three_matches = new_last_three
        self.lose_count+=1
        self.GF += GF
        self.GA += GA

    def IncreaseDraw(self,GF,GA):
        new_last_three = ['D']
        new_last_three.append(self.last_three_matches[0])
        new_last_three.append(self.last_three_matches[1])
        self.last_three_matches = new_last_three
        self.draw_count+=1
        self.GF += GF
        self.GA += GA





