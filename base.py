import cv2
import cv2.cv
import numpy as np
from exibir_imagens import mostra_imagens

#Ordem em que a base sera anotada.
la1 = [111, 128, 77, 82, 86, 115, 90, 81, 13, 8, 47, 5, 93, 36, 26, 53, 54, 79,
       18, 73, 40, 125, 87, 11, 14, 15, 123, 37, 74, 99, 59, 42, 67, 23, 38,
       116, 12, 100, 122, 95, 17, 6, 45, 94, 127, 39, 27, 109, 19, 65, 52, 105,
       10, 120, 9, 21, 31, 44, 22, 85, 3, 49, 28, 68, 50, 25, 43, 46, 35, 71, 80,
       51, 34, 20, 126, 56, 1, 30, 7, 96, 33, 76, 4, 57, 24, 106, 64, 55, 32, 16,
       108, 63, 101, 118, 60, 107, 124, 48, 113, 70, 110, 114, 61, 97, 104, 83,
       117, 112, 98, 92, 91, 62, 75, 102, 66, 121, 58, 29, 88, 119, 89, 72, 103,
       84, 41, 0, 2, 69, 78]

shape_imagens = (4160, 3120) #altura, largura
shape_patch = (500, 500) #altura, largura

class Lamina:
    #Recebe opcionalmente como parametros as coordenadas do canto superior 
    #esquerdo e o formato (largura e altura) do retangulo no qual a elipse
    #encaixada no GIMP esta inscrita.
    def __init__(self, canto = None, shape = None):
        if canto is None:
            self.raio = None
            self.centro = None
        else:
            self.raio = (shape[0] + shape[1])/4
            self.centro = (canto[0] + self.raio, canto[1] + self.raio) 

    #Retorna uma imagem binaria que serve como mascara para a regiao da lamina.
    def get_imagem(self):
        imagem = np.zeros(shape_imagens, dtype=np.uint8)
        cv2.circle(imagem, self.centro, self.raio, 255, thickness=-1)
        return imagem

    #Checa se um ponto esta dentro da lamina.
    def esta_dentro(self, p):
        return ((self.centro[0] - p[0])**2 + (self.centro[1] - p[1])**2
                < self.raio**2)

    #Checa se a regiao de um patch esta completamente dentro da lamina atraves
    #da checagem dos quatro cantos.
    def patch_esta_dentro(self, patch):
        h, w = shape_patch
        x, y = patch.canto
        return (self.esta_dentro((x, y)) and self.esta_dentro((x + w, y)) and 
                self.esta_dentro((x + w, y + h)) and self.esta_dentro((x, y + h)))
    
    def avaliar_lamina(self, tentativa, analise=False, indice=None):
        im = self.get_imagem()
        
        import numpy as np
        comp = np.zeros(shape_imagens + (3,), dtype=np.uint8)
        comp[:,:,0] = im
        comp[:,:,2] = tentativa
             
        hist = cv2.calcHist([comp], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
        perdidos = hist[255,0,0] #pixels da lamina anotada que nao foram pegos
        excesso = hist[0,0,255] #pixels que foram pegos a mais
        #Atribui mais peso a area exterior a lamina que foi pega e pode,
        #nos proximos passos, gerar regioes nao legitimas na periferia da lamina.
        nota = perdidos + 3*excesso 
        nota = nota/(shape_imagens[0]*shape_imagens[1]) #normaliza
        nota = 1-nota #quanto maior melhor
                     
        if analise:
            if indice is None:
                mostra_imagens([comp], "")
            else:
                original = cv2.imread("base\\" + str(indice) + ".jpg", cv2.IMREAD_COLOR)
                rosa = np.array([255, 0, 255], dtype="uint8")
                comum = cv2.inRange(comp, rosa, rosa)
                contours, hierarchy = cv2.findContours(comum, 
                                               cv2.RETR_CCOMP,
                                               cv2.CHAIN_APPROX_NONE)
                cv2.drawContours(original, contours, -1, (0,255,0), 3)
                mostra_imagens([comp, original], "")
            print "Pixels perdidos: " + str(perdidos)
            print "Pixels pegos em excesso: " + str(excesso)
            print "\n\n"

        return nota
            
class Patch:
    def __init__(self, canto = (None, None), indice = None):
        self.canto = canto #(x, y) canto superior esquerdo
        self.indice = indice
        #anotacoes
        
    def get_imagem(self):
        x, y = self.canto
        h, w = shape_patch
        imagem = cv2.imread("base\\" + str(self.indice) + ".jpg", cv2.IMREAD_COLOR)
        return imagem[y : y + h, x : x + w]
        
class Imagem:
    def __init__(self, indice):
        self.indice = indice
        self.lamina = None
        self.patch = None
        self.foco = None
        self.obstruida = None
        
    def get_patch(self):
        if self.lamina is None:
            raise Exception("Voce nao definiu a lamina!")
        elif self.patch is None:
            import random as rd
            rd.seed(self.indice)
            h, w = shape_imagens
            patch = Patch(canto = (rd.randint(0, h), rd.randint(0, w)))
            while not self.lamina.patch_esta_dentro(patch):
                patch.canto = (rd.randint(0, h), rd.randint(0, w))
            patch.indice = self.indice
            self.patch = patch
            return patch
        else:
            return self.patch      
            
    def get_imagem(self):
        return cv2.imread("base\\" + str(self.indice) + ".jpg", cv2.IMREAD_COLOR)
    

class Base:
    def __init__(self):
        self.imagens = [Imagem(indice = i) for i in range(1, 130)]

    def anotar_lamina(self):
        for i in la1:
            if self.imagens[i-1].lamina is None:
                print "A proxima lamina a ser anotada eh a " + str(i)
                x = int(raw_input("Canto x: "))
                y = int(raw_input("Canto y: "))
                w = int(raw_input("Largura: "))
                h = int(raw_input("Altura: "))
                self.imagens[i].lamina = Lamina(i, canto = (x,y), shape = (w, h))
                return
        print "Todas as laminas foram anotadas"
        return
    
    def get_imagens(self, condicoes):
        return [x for x in self.imagens if condicoes(x)] 
        
    def salvar(self):
        import pickle
        with open("anotacoes_base\\anotacoes.pkl", "wb") as f:
            pickle.dump(self, f)
            f.close()
      
         
import pickle
with open("anotacoes_base\\anotacoes.pkl", "rb") as f:
    base = pickle.load(f)
    f.close()