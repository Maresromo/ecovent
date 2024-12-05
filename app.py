from shiny import render
from shiny.express import input, ui
from shiny.ui import page_navbar
from shiny import reactive

from functools import partial
from datetime import datetime
from matplotlib.gridspec import GridSpec
from windrose import WindroseAxes, plot_windrose
from windrose import WindAxes

import pandas as pd
import seaborn as sbn
import matplotlib.pyplot as plt
import numpy as np

meses = ['Ene.', 'Feb.', 'Mar.', 'Abr.', 'May.', 'Jun.', 'Jul.', 'Ago.', 'Sep.', 'Oct.', 'Nov.', 'Dic.']
RUOA = pd.read_csv("./data/R-U-O-A_completo.csv",index_col=0, parse_dates=True)
To = RUOA.Temp_Avg.groupby(by=[RUOA.index.strftime("%m"),RUOA.index.strftime("%H:%M")]).mean().unstack().T.copy()
T_confort = (0.31 * To.mean() + 17.8)

Zona_confort = pd.DataFrame()
Zona_confort['T_confort'] = T_confort
Zona_confort['T_exterior'] = To.mean()
Zona_confort['Lim_sup'] = T_confort + 2.5
Zona_confort['Lim_inf'] = T_confort - 2.5

To_diario = RUOA.Temp_Avg.groupby(by=[
    RUOA.index.strftime("%m-%d"),  # Día completo
    RUOA.index.strftime("%H:%M")     # Hora y minuto
]).mean().unstack().T.copy()

HR = RUOA.RH_Avg.groupby(by=[RUOA.index.strftime("%m"),RUOA.index.strftime("%H:%M")]).mean().unstack().T.copy()
HR_diario = RUOA.RH_Avg.groupby(by=[
    RUOA.index.strftime("%m-%d"),  # Día completo
    RUOA.index.strftime("%H:%M")     # Hora y minuto
]).mean().unstack().T.copy()


ui.page_opts(
    title="EcoVent.app",  
    page_fn=partial(page_navbar, id="page"),  
)

with ui.nav_panel("Acerca de"):  

    ui.h3("¿Qué es?")
    '''EcoVent es una app que tiene como objetivo brindar una herramienta para analizar la temperatura y humedad relativa del exterior con 
    el fin de determinar en qué horarios es más conveniente utilizar la ventilación natural. De esta forma reducir nuestro consumo en sistemas
    de calefacción, refigeración y control de humedad. La app también puede ser utilizada para analizar la temperatura y humedad relativa para
    otros fines distintos a los establecidos en este texto.'''
    ui.h3("¿Cómo usa?")
    '''EcoVent es una app que tiene como objetivo brindar una herramienta para analizar la temperatura y humedad relativa del exterior, con 
    el fin de determinar en qué horarios es más conveniente utilizar la ventilación natural. De esta forma reducir nuestro consumo en sistemas
    de calefacción, refrigeración y control de humedad'''
    ui.input_select(
        "lugar",
        "¿Qué lugar deseas analizar?",
        {
            "./data/R-U-O-A_completo.csv": "Temixco, en un futuro tendrá más opciones :)",
        }
    ), 
    ui.h3("Glosario")
    ui.p('''Humedad relativa: Razón de fracción molar de vapor a la fracción molar de aire saturado.''')
    ui.p('''Temperatura de confort [°C]: La temperatura de confort es aquella temperatura operativa (considera temperatura del aire, temperatura media 
    radiante y velocidad del aire) en la cual se consigue un voto de sensación térmica de cero. Para está app se utilizó el modelo ASHRAE 55 (2013) 
    ya que se considera un modelo adaptativo global, porque que su base de datos incluye mediciones de 160 edificios en 4 continentes. 
    Es aplicable en diversos climas.''')
    ui.p('''Temperatura de bulbo seco [°C]: Es la temperatura del aire con un termómetro con el sensor seco. Se suele referir a ella como temperatura 
         del aire.''')
    ui.p('''Temperatura operativa [°C]: Considera la temperatura del aire, temperatura radiante media y velocidad del aire. Representa la temperatura 
         uniforme de un espacio imaginario de color negro que 
         produce la misma pérdida de calor por radiación y convección que el ambiente real.''')
    ui.p('''Velocidad del aire [m/s]: Distancia que recorre una partícula de aire en una unidad de tiempo.''')
    ui.h3("Autor")
    ui.p('''Romo Eligio Erick Jahir''')

    
with ui.nav_panel("Temperatura exterior"):  
    ui.h3("Temperatura de confort")
    '''La temperatura de confort es aquella temperatura operativa (considera temperatura del aire, temperatura media radiante y velocidad del aire) 
    en la cual se consigue un voto de sensación térmica de cero (ni frío ni calor). Para esta app se utilizó el modelo ASHRAE 55 (2013) con un 
    porcentaje de aceptación del 90%; esto representa el área gris o zona de confort.''',  

    @render.plot()  
    def zona_confort():
        
        fig, ax = plt.subplots(figsize=(10, 6))

        # Gráfica principal
        ax.plot(Zona_confort['T_confort'], label='T_confort', color='blue')
        ax.plot(Zona_confort['T_exterior'], label='T_exterior', color='green')
        ax.fill_between(
            Zona_confort.index,
            Zona_confort['Lim_inf'],
            Zona_confort['Lim_sup'],
            color='gray',
            alpha=0.3,
            label='Zona de confort'
        )

        # Personalizar la gráfica
        ax.set_title('Zona de confort con la norma ASHRAE 55 (2013)')
        ax.set_xlabel('Mes')
        ax.set_ylabel('Temperatura [°C]')
        ax.set_xticks(ticks=range(len(meses)))
        ax.set_xticklabels(meses)

        # Personalizar el eje Y para intervalos de 0.5 grados
        min_y = Zona_confort['Lim_inf'].min() - 1  # Margen inferior
        max_y = Zona_confort['Lim_sup'].max() + 1  # Margen superior
        ax.set_yticks(np.arange(np.floor(min_y), np.ceil(max_y) + 0.5, 0.5))

        ax.legend()
        ax.grid()
    @render.text
    def TC_lim():
        return f'''Límite inferior minimo anual = {round(Zona_confort['Lim_inf'].min(),2)}°C, 
        Límite superior máximo anual = {round(Zona_confort['Lim_sup'].max(),2)}°C'''
    ui.h3(" ")    
    ui.h3("Temperatura promedios mensuales")
    ui.p('''La principal variable que determina si es conveniente utilizar la ventilación natural en un momento dado es la 
    temperatura del aire. En esta sección se representan el promedio de cada hora en los datos de cada mes para los 
    años con los que se cuentan, 8 en el caso de Temixco. Esta gráfica permite dar un vistazo a grandes rasgos del 
    comportamiento de la temperatura a lo largo del año. Para una mejor visualización, usted puede modificar las 
    siguientes características:''')
    with ui.layout_columns():  
        with ui.card():  
            ui.card_header("Tiempo")
            ui.input_slider("horario_anio", "Horario [horas]", min=0, max=23, value=[0, 23])  
            ui.input_slider("meses_anio", "Periodo [meses]", min=1, max=12, value=[0, 23])  


        with ui.card():  
            ui.card_header("Temperatura de confort")
            ui.input_select(  
            "AjusteTo_Tc",  
            "¿Deseas ajustar el rango de temperatura al de la zona de confort del periodo escogido?",  
            {"No": "No", "Si": "Si"},  
            )  

            ui.input_action_button("explicacionHMA", "Explicación")

            @reactive.effect
            @reactive.event(input.explicacionHMA)
            def show_important_message():
                m = ui.modal(  
                    "Si ajustas el rango de temperaturas a los valores de la zona de confort podrás ver claramente los horarios y meses en los que hay disconfort, si el color es el azul más oscuro, eso indica disconfort frío, mientras que si es el rojo más oscuro, es señal de disconfort cálido",  
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

        with ui.card():  
            ui.card_header("Temperatura exterior")
            ui.input_slider("temperaturas", "Rango de temperatura [°C]", min=0, max=45, value=[To.stack().min(), To.stack().max()],step=0.01)
            @render.text
            def Tmin_Tmax_anual():
                return f"Tmin_anual = {round(To.stack().min(),2)}°C, Tmax_anual = {round(To.stack().max(),2)}°C"
            ui.input_numeric("delta", "Delta de temperatura [°C]", 1, min=0.5, max=10)  
    
    @render.plot(alt="Heatmap_anual") 
    # def operaciones_heatmap1():


    def Heatmap_anual():  
        matriz_anio = To
        matriz_anio.columns = meses

        desde_hora = input.horario_anio()[0]
        hasta_hora = input.horario_anio()[1]

        desde_mes = input.meses_anio()[0]
        hasta_mes = input.meses_anio()[1]

        if input.AjusteTo_Tc() == "Si":
            desde = Zona_confort['Lim_inf'].iloc[input.meses_anio()[0]:input.meses_anio()[1]].min()
            hasta = Zona_confort['Lim_sup'].iloc[input.meses_anio()[0]:input.meses_anio()[1]].max()
        else:
            desde = input.temperaturas()[0]
            hasta = input.temperaturas()[1]

        matriz_anio = To.iloc[desde_hora:hasta_hora+1, desde_mes-1:hasta_mes] 

        delta = input.delta()

        fig, ax = plt.subplots(figsize=(10, 6))
        # Crear el heatmap sin barra de color
        sbn.heatmap(matriz_anio, cmap="jet", vmin=desde, vmax=hasta, cbar=False)

        # Mostrar el heatmap con imshow
        p = ax.imshow(matriz_anio, aspect="auto", cmap="jet", vmin=desde, vmax=hasta)

        # Crear la colorbar
        cbar = fig.colorbar(p, label="To [°C]")

        # Generar ticks intermedios con np.arange y agregar los límites inferior y superior
        ticks_intermedios = np.arange(desde, hasta, delta)  # Valores intermedios
        ticks_completos = np.concatenate(([desde], ticks_intermedios, [hasta]))  # Incluyendo límites

        # Redondear los valores de la lista al primer decimal
        ticks_completos = [round(val, 1) for val in ticks_completos]

        # Establecer los ticks completos en la colorbar
        cbar.set_ticks(ticks_completos)

        # Etiquetar los ticks
        cbar.set_ticklabels([f"{tick}" for tick in ticks_completos])

        # Mostrar los límites inferiores y superiores en ambos extremos de la colorbar
        cbar.ax.tick_params(which="both", direction="out", top=True, bottom=True)

        # Personalizar los valores del eje Y para que estén horizontales
        ax.tick_params(axis="y", labelrotation=0)  # Configuración para etiquetas horizontales

        # Personalizar el título y los ejes
        plt.title("Temperatura promedios mensuales", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tiempo [h]")
        ax.set_xlabel("Mes")

        return ax
    
    ui.h3("Temperatura promedios diarios")
    'Así mismo, estas temperaturas representan el promedio de cada hora para cada día para los años con los que se cuentan, la ventaja que tiene de los promedios mensuales es una mayor resolución de los datos, un uso más preciso de la temperatura de confort. Para una mejor visualización, usted puede modificar las siguientes características:'
    with ui.layout_columns(): 
        with ui.card():  
            ui.card_header("Tiempo")
            ui.input_slider("horario_mes", "Horario [horas]", min=0, max=23, value=[0, 23])  
            ui.input_select(
                "mes",
                "¿Qué mes deseas analizar?",
                {
                    "01": "Enero",
                    "02": "Febrero",
                    "03": "Marzo",
                    "04": "Abril",
                    "05": "Mayo",
                    "06": "Junio",
                    "07": "Julio",
                    "08": "Agosto",
                    "09": "Septiembre",
                    "10": "Octubre",
                    "11": "Noviembre",
                    "12": "Diciembre"
                }
            ), 
            ui.input_slider("dias_mes", "Periodo (dias)", min=1, max=31, value=[0, 31])             



        with ui.card():  
            ui.card_header("Temperatura de confort")
            ui.input_select(  
                "Ajuste_diario_To_Tc",  
                "¿Deseas ajustar el rango de temperatura al de la zona de confort del periodo escogido?",  
                {"No": "No", "Si": "Si"},  
                )  

            ui.input_action_button("explicacionHMM", "Explicación")

            @reactive.effect
            @reactive.event(input.explicacionHMM)
            def show_important_message():
                m = ui.modal(  
                    "Si ajustas el rango de temperaturas a los valores de la zona de confort podrás ver claramente los horarios y días en los que hay disconfort, si el color es el azul más oscuro, eso indica disconfort frío, mientras que si es el rojo más oscuro, es señal de disconfort cálido",  
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

        with ui.card():  
            ui.input_slider(
                "temperaturas_dia", "Rango de temperatura [°C]", 
                min=0, max=45, 
                value=[round(To.stack().min(),2), 
                    round(To.stack().max(),2)]
                ,step=0.01)
            
            @render.text
            def Tmin_Tmax_mensual():
                return f'''Tmin_dia = {round(To_diario[[col for col in To_diario.columns if col.startswith(str(input.mes()))]].stack().min(),2)}°C, 
                        Tmax_dia = {round(To_diario[[col for col in To_diario.columns if col.startswith(str(input.mes()))]].stack().max(),2)}°C"'''
            
            ui.input_numeric("delta_dia", "Delta de temperatura [°C]", 1, min=0.5, max=10)  
    
    @render.plot(alt="Heatmap_mensual") 
    # def operaciones_heatmap1():


    def Heatmap_mensual():  
        matriz_mes = To_diario

        desde_hora = input.horario_mes()[0]
        hasta_hora = input.horario_mes()[1]

        desde_dia = input.dias_mes()[0]
        hasta_dia = input.dias_mes()[1]

        if input.Ajuste_diario_To_Tc() == "Si":
            desde = Zona_confort['Lim_inf'].iloc[int(input.mes())]
            hasta = Zona_confort['Lim_sup'].iloc[int(input.mes())]
        else:
            desde = input.temperaturas_dia()[0]
            hasta = input.temperaturas_dia()[1]

        matriz_mes = matriz_mes[[col for col in To_diario.columns if col.startswith(str(input.mes()))]] 
        matriz_mes = matriz_mes.iloc[desde_hora:hasta_hora+1, desde_dia-1:hasta_dia] 
        
        delta = input.delta_dia()

        fig, ax = plt.subplots(figsize=(10, 6))
        # Crear el heatmap sin barra de color
        sbn.heatmap(matriz_mes, cmap="jet", vmin=desde, vmax=hasta, cbar=False)

        # Mostrar el heatmap con imshow
        p = ax.imshow(matriz_mes, aspect="auto", cmap="jet", vmin=desde, vmax=hasta)

        # Crear la colorbar
        cbar = fig.colorbar(p, label="To [°C]")

        # Generar ticks intermedios con np.arange y agregar los límites inferior y superior
        ticks_intermedios = np.arange(desde, hasta, delta)  # Valores intermedios
        ticks_completos = np.concatenate(([desde], ticks_intermedios, [hasta]))  # Incluyendo límites

        # Redondear los valores de la lista al primer decimal
        ticks_completos = [round(val, 1) for val in ticks_completos]

        # Establecer los ticks completos en la colorbar
        cbar.set_ticks(ticks_completos)

        # Etiquetar los ticks
        cbar.set_ticklabels([f"{tick}" for tick in ticks_completos])

        # Mostrar los límites inferiores y superiores en ambos extremos de la colorbar
        cbar.ax.tick_params(which="both", direction="out", top=True, bottom=True)

        # Personalizar los valores del eje Y para que estén horizontales
        ax.tick_params(axis="y", labelrotation=0)  # Configuración para etiquetas horizontales

        # Personalizar el título y los ejes
        plt.title("Temperatura promedios diarios", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tiempo [h]")
        ax.set_xlabel("Mes")

        return ax
    
    ui.h3("Conclusión")
    'En términos de temperatura, las horas en las que resulta conveniente la ventilación natural son aquellas que se encuentran entre los límites de la zona de confort, visibles al activar la opción de ajuste. Esto puede ayudar a tener condiciones confortables en las edificaciones y a ahorrar energía en aqullas que cuentan con sistemas de enfriamiento y/o calentamiento. Cabe destacar que estos modelos no toman en cuenta la temperatura del aire al interior, por lo tanto, en algunas ocasiones será conveniente aprovechar la ventilación natural, aunque la temperatura del aire exterior se encuentre fuera de la zona de confort.'


#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

with ui.nav_panel("Humedad relativa"):  
    ui.h3("Humedad relativa")
    '''Otra variable importante para determinar si es conveniente el aprovechamiento de la ventilación natural es la humedad relativa (HR) o 
    razón de fracción molar de vapor a la fracción molar de aire saturado (100% HR). Según la norma ASHRAE 55 (2013), para poder alcanzar 
    condiciones confortables, la humedad relativa tiene que ser mayor a 20% para evitar sensaciones de resequedad en piel, ojos y vías
    respiratorias, así como evitar la acumulación de electricidad estática. Así mismo, recomienda que la HR esté por debajo del 60%, esto 
    para evitar sensaciones de bochorno y reducir el crecimiento de hongos y otros microorganismos.''',  
 
    ui.h3("HR promedios mensuales")
    'En esta gráfica se puede observar el comportamiento de la temperatura a lo largo del año. Para una mejor visualización, usted puede modificar las siguientes características:'

    with ui.layout_columns(): 
        with ui.card():  
            ui.card_header("Tiempo")
            ui.input_slider("horario_anio_HR", "Horario [horas]", min=0, max=23, value=[0, 23])  
            ui.input_slider("meses_anio_HR", "Periodo [meses]", min=1, max=12, value=[0, 23])  

        with ui.card():  
            ui.card_header("Ajuste a la norma")
            ui.input_select(  
            "AjusteHR",  
            "¿Deseas ajustar el rango de temperatura a las recomendaciones del ASHRAE 55 (2013)?",  
            {"No": "No", "Si": "Si"},  
            )  

            ui.input_action_button("explicacionHR", "Explicación")

            @reactive.effect
            @reactive.event(input.explicacionHR)
            def show_important_message():
                m = ui.modal(  
                    "Si ajustas el rango al ASHRAE 55 (2013) podrás ver claramente los horarios y meses en los que no se cumple, si el color es el azul más oscuro, eso indica una humedad demasiado baja, mientras que si es el rojo más oscuro, es señal de un exceso de humedad",  
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

        with ui.card():  
            ui.card_header("Humedad")
            ui.input_slider("HR_rango_anio", "Rango de humedad relativa (%)", min=0, max=100, value=[HR.stack().min(), HR.stack().max()],step=0.5)
            @render.text
            def HRmin_HRmax_anual():
                return f"HRmin_anual = {round(HR.stack().min(),2)}%, HRmax_anual = {round(HR.stack().max(),2)}%"
            ui.input_numeric("delta_HR_anual", "Delta de HR (%)", 10, min=0.5, max=50)  
    
    @render.plot(alt="Heatmap_anual") 
    # def operaciones_heatmap1():


    def Heatmap_anual_HR():  
        matriz_anio = HR
        matriz_anio.columns = meses

        desde_hora = input.horario_anio_HR()[0]
        hasta_hora = input.horario_anio_HR()[1]

        desde_mes = input.meses_anio_HR()[0]
        hasta_mes = input.meses_anio_HR()[1]

        if input.AjusteHR() == "Si":
            desde = 20
            hasta = 60
        else:
            desde = input.HR_rango_anio()[0]
            hasta = input.HR_rango_anio()[1]

        matriz_anio = HR.iloc[desde_hora:hasta_hora+1, desde_mes-1:hasta_mes] 

        delta = input.delta_HR_anual()

        fig, ax = plt.subplots(figsize=(10, 6))
        # Crear el heatmap sin barra de color
        sbn.heatmap(matriz_anio, cmap="jet", vmin=desde, vmax=hasta, cbar=False)

        # Mostrar el heatmap con imshow
        p = ax.imshow(matriz_anio, aspect="auto", cmap="jet", vmin=desde, vmax=hasta)

        # Crear la colorbar
        cbar = fig.colorbar(p, label="HR [%]")

        # Generar ticks intermedios con np.arange y agregar los límites inferior y superior
        ticks_intermedios = np.arange(desde, hasta, delta)  # Valores intermedios
        ticks_completos = np.concatenate(([desde], ticks_intermedios, [hasta]))  # Incluyendo límites

        # Redondear los valores de la lista al primer decimal
        ticks_completos = [round(val, 1) for val in ticks_completos]

        # Establecer los ticks completos en la colorbar
        cbar.set_ticks(ticks_completos)

        # Etiquetar los ticks
        cbar.set_ticklabels([f"{tick}" for tick in ticks_completos])

        # Mostrar los límites inferiores y superiores en ambos extremos de la colorbar
        cbar.ax.tick_params(which="both", direction="out", top=True, bottom=True)

        # Personalizar los valores del eje Y para que estén horizontales
        ax.tick_params(axis="y", labelrotation=0)  # Configuración para etiquetas horizontales

        # Personalizar el título y los ejes
        plt.title("Humedad relativa promedios mensuales", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tiempo [h]")
        ax.set_xlabel("Mes")

        return ax
    
    ui.h3("HR promedios diarios")
    'Así mismo, estos datos representan el promedio de cada hora para cada día para los años con los que se cuentan, la ventaja que tiene de los promedios mensuales es una mayor resolución. Para una mejor visualización, usted puede modificar las siguientes características:'
    with ui.layout_columns(): 
        with ui.card():  
            ui.card_header("Tiempo")
            ui.input_slider("horario_mes_HR", "Horario [horas]", min=0, max=23, value=[0, 23])  
            ui.input_select(
                "mes_HR",
                "¿Qué mes deseas analizar?",
                {
                    "01": "Enero",
                    "02": "Febrero",
                    "03": "Marzo",
                    "04": "Abril",
                    "05": "Mayo",
                    "06": "Junio",
                    "07": "Julio",
                    "08": "Agosto",
                    "09": "Septiembre",
                    "10": "Octubre",
                    "11": "Noviembre",
                    "12": "Diciembre"
                }
            ), 
            ui.input_slider("dias_mes_HR", "Periodo (dias)", min=1, max=31, value=[0, 31])             
        with ui.card():  
            ui.card_header("Ajuste a la norma")
            ui.input_select(  
            "AjusteHR_diario",  
            "¿Deseas ajustar el rango de humedad relativa a las recomendaciones del ASHRAE 55 (2013)?",  
            {"No": "No", "Si": "Si"},  
            )  

            ui.input_action_button("explicacionHR_diario", "Explicación")

            @reactive.effect
            @reactive.event(input.explicacionHR_diario)
            def show_important_message():
                m = ui.modal(  
                    "Si ajustas el rango al ASHRAE 55 (2013) podrás ver claramente los horarios y días en los que no se cumple, si el color es el azul más oscuro, eso indica una humedad demasiado baja, mientras que si es el rojo más oscuro, es señal de un exceso de humedad",  
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)
        with ui.card():  
            ui.card_header("Humedad")
            ui.input_slider("HR_rango_mes", "Rango de humedad relativa (%)", min=0, max=100, 
                value=[round(HR.stack().min(),2), 
                    round(HR.stack().max(),2)]
                ,step=0.5)
            
            @render.text
            def HR_dia_min_max():
                return f'''HRmin_dia = {round(HR_diario[[col for col in HR_diario.columns if col.startswith(str(input.mes_HR()))]].stack().min(),2)}%, 
                        HRmax_dia = {round(HR_diario[[col for col in HR_diario.columns if col.startswith(str(input.mes_HR()))]].stack().max(),2)}%"'''
            
            ui.input_numeric("delta_dia_HR", "Delta de humrdad relativa [%]", 20, min=0.5, max=50)  
            
    @render.plot(alt="Heatmap_mensual") 
    # def operaciones_heatmap1():


    def Heatmap_mensual_HR():  
        matriz_mes = HR_diario

        desde_hora = input.horario_mes_HR()[0]
        hasta_hora = input.horario_mes_HR()[1]

        desde_dia = input.dias_mes_HR()[0]
        hasta_dia = input.dias_mes_HR()[1]

        if input.AjusteHR_diario() == "Si":
            desde = 20
            hasta = 60
        else:
            desde = input.HR_rango_mes()[0]
            hasta = input.HR_rango_mes()[1]

        matriz_mes = matriz_mes[[col for col in HR_diario.columns if col.startswith(str(input.mes_HR()))]] 
        matriz_mes = matriz_mes.iloc[desde_hora:hasta_hora+1, desde_dia-1:hasta_dia] 
        
        delta = input.delta_dia_HR()

        fig, ax = plt.subplots(figsize=(10, 6))
        # Crear el heatmap sin barra de color
        sbn.heatmap(matriz_mes, cmap="jet", vmin=desde, vmax=hasta, cbar=False)

        # Mostrar el heatmap con imshow
        p = ax.imshow(matriz_mes, aspect="auto", cmap="jet", vmin=desde, vmax=hasta)

        # Crear la colorbar
        cbar = fig.colorbar(p, label="To [%]")

        # Generar ticks intermedios con np.arange y agregar los límites inferior y superior
        ticks_intermedios = np.arange(desde, hasta, delta)  # Valores intermedios
        ticks_completos = np.concatenate(([desde], ticks_intermedios, [hasta]))  # Incluyendo límites

        # Redondear los valores de la lista al primer decimal
        ticks_completos = [round(val, 1) for val in ticks_completos]

        # Establecer los ticks completos en la colorbar
        cbar.set_ticks(ticks_completos)

        # Etiquetar los ticks
        cbar.set_ticklabels([f"{tick}" for tick in ticks_completos])

        # Mostrar los límites inferiores y superiores en ambos extremos de la colorbar
        cbar.ax.tick_params(which="both", direction="out", top=True, bottom=True)

        # Personalizar los valores del eje Y para que estén horizontales
        ax.tick_params(axis="y", labelrotation=0)  # Configuración para etiquetas horizontales

        # Personalizar el título y los ejes
        plt.title("Humedad relativa promedios diarios", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tiempo [h]")
        ax.set_xlabel("Mes")

        return ax
    
    ui.h3("Conclusión")
    '''En términos de humedad relavita, las horas en las que resulta conveniente la ventilación natural son aquellas que se 
    encuentran entre los Límites de la norma ASHRAE 55 (2013), visibles al activar la opción de ajuste. Esto puede ayudar a 
    mantener dentro de los límites la humedad del ambiente, con ello se puede reducir o evitar el uso de sistemas de control de
    humedad.'''
